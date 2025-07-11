import csv
import logging
import tempfile
from abc import abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable

import numpy as np
import requests
import scipy
import tensorflow as tf

from bark_monitor.base_sync import BaseSync
from bark_monitor.recorders.base_recorder import BaseRecorder
from bark_monitor.recorders.recording import Activity, Recording


class WaveRecorder(BaseRecorder):
    """A recorder that records a wav file"""

    def __init__(
        self,
        sync: BaseSync,
        output_folder: Path,
        sampling_time_bark_seconds: int | None = 1,
        http_url: str | None = None,
        framerate: int = 16000,
        chunk: int = 4096,
        send_text_callback: Callable[[str], None] | None = None,
    ) -> None:
        """
        `api_key` is the key of telegram bot and `config_folder` is the folder with the
        chats config for telegram bot. `output_folder` define where to save the
        recordings. If `accept_new_users` is True new users can register to the telegram
        bot---defaults to False. A bark detection can be run every
        `sampling_time_bark_seconds` on the recording---defaults to none, in which case
        the detection is run after every `self._chunk` samples have been collected
        instead.
        """
        self._sampling_time_bark_seconds = sampling_time_bark_seconds

        self._nn_frames: list[bytes] = []
        self._http_url = http_url

        self._animal_labels = [
            "Animal",
            "Domestic animals, pets",
            "Dog",
            "Bark",
            "Howl",
            "Growling",
            "Bow-wow",
            "Whimper (dog)",
            "Cat",
            "Purr",
            "Meow",
            "Hiss",
        ]

        self._temp_activity: Activity | None = None

        super().__init__(
            sync=sync,
            output_folder=output_folder,
            framerate=framerate,
            chunk=chunk,
            send_text_callback=send_text_callback,
        )

    @staticmethod
    def class_names_from_csv(class_map_csv_text: str) -> list[str]:
        class_names = []
        with tf.io.gfile.GFile(class_map_csv_text) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                class_names.append(row["display_name"])
        return class_names

    @staticmethod
    def ensure_sample_rate(
        original_sample_rate: int,
        waveform: np.ndarray,
        desired_sample_rate: int = 16000,
    ) -> tuple[int, np.ndarray]:
        if original_sample_rate != desired_sample_rate:
            desired_length = int(
                round(float(len(waveform)) / original_sample_rate * desired_sample_rate)
            )
            waveform = scipy.signal.resample(waveform, desired_length)
        return desired_sample_rate, waveform

    @abstractmethod
    def _detect(self, wave_file: Path) -> str:
        raise NotImplementedError()

    def _record_loop(self) -> None:
        self._start_stream()
        self._bark_logger.info("Recording started")

        assert self._stream is not None

        while self.running:
            if self.is_paused:
                continue

            # Exception overflow is needed when running on the rpi
            # Because processing is slow and frame can be lost.
            data = self._stream.read(self._chunk, exception_on_overflow=False)
            self._nn_frames.append(data)
            duration = int((len(self._nn_frames) * self._chunk) / self._fs)

            # Guard clause: do not run bark detection if recording time is less than
            # `self._sampling_time_bark_seconds`
            if (
                self._sampling_time_bark_seconds is not None
                and duration < self._sampling_time_bark_seconds
            ):
                continue

            with tempfile.TemporaryDirectory() as tmpdirname:
                nn_recording = self._save_recording_to(
                    self._nn_frames, Path(tmpdirname, "rec.wav")
                )
                self._analyse_recording(nn_recording)

            # remove temporary recording
            self._nn_frames = []

        self._stop_stream()

    def _analyse_recording(self, nn_recording: Path) -> None:
        label = self._detect(nn_recording)
        self._bark_logger.info("detected " + label)

        payload = dict.fromkeys(self._animal_labels, 0)

        if label in self._animal_labels:
            payload[label] = 1
            # notify
            if self.send_text_callback is not None:
                self.send_text_callback("detected: " + label)

            # save all frame to make one large recording
            self._frames += self._nn_frames

            # increase time barked in state
            recording = Recording.read(
                output_folder=self.output_folder, sync_service=self._sync
            )
            duration = timedelta(
                seconds=(len(self._nn_frames) * self._chunk) / self._fs
            )
            recording.add_time_barked(duration)

            if self._temp_activity is None:
                self._temp_activity = Activity(
                    label=label,
                    date=datetime.now(),
                    duration=duration,
                    audio_path=Path(""),
                )
            else:
                self._temp_activity.duration += duration

        elif len(self._frames) > 0:
            recording = Recording.read(self.output_folder, sync_service=self._sync)
            label = ""
            time = None
            for activity in recording.activity_tracker:
                if time is None or time < activity.date:
                    time = activity.date
                    label = activity.label
            audio_path = self._save_recording(self._frames, label)

            # Update activity and save to the recodings
            assert self._temp_activity is not None
            self._temp_activity.audio_path = audio_path

            recording.add_activity(self._temp_activity)

            self._frames = []

        try:
            if self._http_url is not None:
                requests.post(self._http_url, json=payload)
        except Exception as e:
            self._bark_logger = logging.getLogger("bark_monitor")
            assert self._http_url is not None
            self._bark_logger.error(
                "Error " + str(e) + "sending data to http address: " + self._http_url
            )
