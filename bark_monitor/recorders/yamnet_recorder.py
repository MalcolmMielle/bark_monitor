import csv
import tempfile
from datetime import timedelta
from pathlib import Path

import numpy as np
import scipy
import tensorflow as tf
import tensorflow_hub as hub
from scipy.io import wavfile

from bark_monitor.recorders.base_recorder import BaseRecorder
from bark_monitor.recorders.recording import Recording


class YamnetRecorder(BaseRecorder):
    """A recorder using [Yamnet](https://www.tensorflow.org/hub/tutorials/yamnet) to
    detect dog barks.
    """

    def __init__(
        self,
        api_key: str,
        config_folder: str,
        output_folder: str,
        accept_new_users: bool = False,
        sampling_time_bark_seconds: int = 1,
    ) -> None:
        """
        `api_key` is the key of telegram bot and `config_folder` is the folder with the
        chats config for telegram bot. `output_folder` define where to save the
        recordings. If `accept_new_users` is True new users can register to the telegram
        bot---defaults to False. The ML model is run every `sampling_time_bark_seconds`
        on the recording---defaults to 30.
        """
        self._model = hub.load("https://tfhub.dev/google/yamnet/1")

        class_map_path = self._model.class_map_path().numpy()
        self._class_names = YamnetRecorder.class_names_from_csv(class_map_path)
        self._sampling_time_bark_seconds = sampling_time_bark_seconds

        self._nn_frames: list[bytes] = []

        super().__init__(
            api_key=api_key,
            config_folder=config_folder,
            output_folder=output_folder,
            framerate=16000,
            accept_new_users=accept_new_users,
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

    def _detect(self, wave_file: Path) -> str:
        sample_rate, wav_data = wavfile.read(wave_file, "rb")  # type: ignore
        sample_rate, wav_data = YamnetRecorder.ensure_sample_rate(sample_rate, wav_data)
        waveform = wav_data / tf.int16.max
        scores, _, _ = self._model(waveform)
        scores_np = scores.numpy()
        return self._class_names[scores_np.mean(axis=0).argmax()]

    def _record_loop(self) -> None:
        self._start_stream()
        self._bark_logger.info("Recording started")

        assert self._stream is not None

        while self.running:
            if self.is_paused:
                continue

            data = self._stream.read(self._chunk)
            self._nn_frames.append(data)
            duration = int((len(self._nn_frames) * self._chunk) / self._fs)

            # Guard clause: do not run bark detection if recording time is less than
            # `self._sampling_time_bark_seconds`
            if duration < self._sampling_time_bark_seconds:
                continue

            with tempfile.TemporaryDirectory() as tmpdirname:
                nn_recording = self._save_recording(
                    self._nn_frames, Path(tmpdirname, "rec.wav")
                )
                label = self._detect(nn_recording)
                self._bark_logger.info("detected " + label)
                if label in [
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
                ]:
                    # notify
                    self._chat_bot.send_event(label)

                    # save all frame to make one large recording
                    self._frames += self._nn_frames

                    # increase time barked in state
                    recording = Recording.read(self._output_folder)
                    duration = timedelta((len(self._frames) * self._chunk) / self._fs)
                    recording.time_barked += duration

                else:
                    if len(self._frames) > 0:
                        self._save_recording(self._frames)
                        self._frames = []

                # remove temporary recording
                self._nn_frames = []

        self._stop_stream()
