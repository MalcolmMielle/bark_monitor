import wave
from typing import Optional

import numpy as np


class Bark:
    def __init__(self, file_name: str, step: int = 100) -> None:
        """Extract the signal from the audio file `file_name`. The audio filtered by
        keeping data every `step`"""
        self.file_name = file_name
        self._wav_obj = wave.open(f=self.file_name, mode="rb")
        n_samples = self._wav_obj.getnframes()
        signal_wave = self._wav_obj.readframes(n_samples)

        self.signal_array = np.frombuffer(signal_wave, dtype=np.int16)

        self._step = 1
        if step > 1:
            self._step = step
            self.signal_array = self.signal_array[:: self._step]
