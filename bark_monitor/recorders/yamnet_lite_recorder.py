import zipfile
from pathlib import Path

import numpy as np
import tensorflow as tf
from scipy.io import wavfile

from bark_monitor.base_sync import BaseSync
from bark_monitor.recorders.wave_recorder import WaveRecorder


class YamnetLiteRecorder(WaveRecorder):
    """https://tfhub.dev/google/lite-model/yamnet/classification/tflite/1"""

    def __init__(
        self,
        sync: BaseSync,
        output_folder: Path,
        http_url: str | None = None,
        framerate: int = 16000,
    ) -> None:
        model_path = Path("models", "lite-model_yamnet_classification_tflite_1.tflite")
        self._interpreter = tf.lite.Interpreter(str(model_path))
        labels_file = zipfile.ZipFile(model_path).open("yamnet_label_list.txt")
        self._labels = [
            label.decode("utf-8").strip() for label in labels_file.readlines()
        ]

        input_details = self._interpreter.get_input_details()
        self._waveform_input_index = input_details[0]["index"]
        output_details = self._interpreter.get_output_details()
        self._scores_output_index = output_details[0]["index"]

        super().__init__(
            sync=sync,
            output_folder=output_folder,
            sampling_time_bark_seconds=None,
            http_url=http_url,
            framerate=framerate,
            chunk=15600,
        )

    def _detect(self, wave_file: Path) -> str:
        sample_rate, wav_data = wavfile.read(wave_file, "rb")  # type: ignore
        sample_rate, wav_data = WaveRecorder.ensure_sample_rate(sample_rate, wav_data)
        waveform = wav_data / tf.int16.max

        if waveform.shape[0] != self._chunk:
            raise RuntimeError("Wrong sample size for tf lite Yamnet model")

        self._interpreter.resize_tensor_input(
            self._waveform_input_index, [waveform.size], strict=True
        )
        self._interpreter.allocate_tensors()
        self._interpreter.set_tensor(self._waveform_input_index, np.float32(waveform))
        self._interpreter.invoke()
        scores = self._interpreter.get_tensor(self._scores_output_index)

        return self._labels[scores.argmax()]
