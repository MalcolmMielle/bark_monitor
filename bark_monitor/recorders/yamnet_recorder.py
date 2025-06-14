from pathlib import Path
from typing import Callable

import tensorflow as tf
import tensorflow_hub as hub
from scipy.io import wavfile

from bark_monitor.base_sync import BaseSync
from bark_monitor.recorders.wave_recorder import WaveRecorder


class YamnetRecorder(WaveRecorder):
    """A recorder using [Yamnet](https://www.tensorflow.org/hub/tutorials/yamnet) to
    detect dog barks.

    TODO for Rpi use the tflite version:
    https://github.com/tensorflow/examples/blob/master/lite/examples/audio_classification/raspberry_pi/classify.py
    """  # noqa

    def __init__(
        self,
        sync: BaseSync,
        output_folder: Path,
        sampling_time_bark_seconds: int = 1,
        http_url: str | None = None,
        framerate: int = 16000,
        send_text_callback: Callable[[str], None] | None = None,
    ) -> None:
        """
        `api_key` is the key of telegram bot and `config_folder` is the folder with the
        chats config for telegram bot. `output_folder` define where to save the
        recordings. If `accept_new_users` is True new users can register to the telegram
        bot---defaults to False. The ML model is run every `sampling_time_bark_seconds`
        on the recording---defaults to 30.
        """
        self._model = hub.load("https://tfhub.dev/google/yamnet/1")

        assert self._model is not None

        class_map_path = self._model.class_map_path().numpy()
        self._class_names = WaveRecorder.class_names_from_csv(class_map_path)

        super().__init__(
            sync=sync,
            output_folder=output_folder,
            sampling_time_bark_seconds=sampling_time_bark_seconds,
            http_url=http_url,
            framerate=framerate,
            send_text_callback=send_text_callback,
        )

    def _detect(self, wave_file: Path) -> str:
        sample_rate, wav_data = wavfile.read(wave_file, "rb")  # type: ignore
        sample_rate, wav_data = WaveRecorder.ensure_sample_rate(sample_rate, wav_data)
        waveform = wav_data / tf.int16.max
        scores, _, _ = self._model(waveform)
        scores_np = scores.numpy()
        return self._class_names[scores_np.mean(axis=0).argmax()]
