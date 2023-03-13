import wave
from typing import Optional

import numpy as np


class Bark:
    def __init__(self, file_name: str) -> None:
        self.file_name = file_name
        wav_obj = wave.open(f=self.file_name, mode="rb")
        n_samples = wav_obj.getnframes()
        signal_wave = wav_obj.readframes(n_samples)

        self.signal_array = np.frombuffer(signal_wave, dtype=np.int16)
        self.signal_array = self.signal_array[self.signal_array > 0]
        self.signal_array = self.signal_array[::100]
