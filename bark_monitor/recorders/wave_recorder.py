import csv
import tempfile
from abc import abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import numpy as np
import requests
import scipy
import tensorflow as tf

from bark_monitor.recorders.base_recorder import BaseRecorder
from bark_monitor.recorders.recording import Recording


class WaveRecorder(BaseRecorder):
    """A recorder that records a wav file"""

    def __init__(
        self,
        api_key: str,
        config_folder: str,
        output_folder: str,
        accept_new_users: bool = False,
        sampling_time_bark_seconds: Optional[int] = 1,
        http_url: Optional[str] = None,
        framerate: int = 16000,
        chunk: int = 4096,
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

        super().__init__(
            api_key=api_key,
            config_folder=config_folder,
            output_folder=output_folder,
            framerate=framerate,
            accept_new_users=accept_new_users,
            chunk=chunk,
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
                nn_recording = self._save_recording(
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
            self._chat_bot.send_event(label)

            # save all frame to make one large recording
            self._frames += self._nn_frames

            # increase time barked in state
            recording = Recording.read(self.output_folder)
            duration = timedelta(
                seconds=(len(self._nn_frames) * self._chunk) / self._fs
            )
            recording.add_time_barked(duration)

            # Log in activity logger
            recording.add_activity(datetime.now(), label)

        elif len(self._frames) > 0:
            self._save_recording(self._frames)
            self._frames = []

        if self._http_url is not None:
            requests.post(self._http_url, json=payload)
