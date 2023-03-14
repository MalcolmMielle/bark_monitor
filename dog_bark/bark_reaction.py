from pathlib import Path

import numpy as np
from playsound import playsound


class BarkReaction:
    def __init__(self, bark_level: int = 20000) -> None:
        self._bark_level = bark_level

    def is_bark(self, signal: bytes):
        np_data = np.frombuffer(signal, dtype=np.int16)
        max_val = np.amax(np_data)
        if max_val >= self._bark_level:
            return True
        return False

    def react(self, signal: bytes) -> None:
        if self.is_bark(signal):
            playsound(Path("sounds", "calm.wav").resolve())
