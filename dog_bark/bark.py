import datetime
import wave

import numpy as np
from scipy.signal import hilbert


class Bark:
    def __init__(
        self, file_name: str, step: int = 100, threshold: float = 4000
    ) -> None:
        """Extract the signal from the audio file `file_name`. The audio filtered by
        keeping data every `step`"""
        self.file_name = file_name
        self.threshold = threshold
        self._wav_obj = wave.open(f=self.file_name, mode="rb")
        n_samples = self._wav_obj.getnframes()
        signal_wave = self._wav_obj.readframes(n_samples)

        signal_array = np.frombuffer(signal_wave, dtype=np.int16)

        self._step = 1
        if step > 1:
            self._step = step
            signal_array = signal_array[:: self._step]

        analytic_signal = hilbert(signal_array)
        self.amplitude_envelope = np.abs(analytic_signal)
        self.amplitude_envelope = np.clip(self.amplitude_envelope, self.threshold, None)
        self.amplitude_envelope[self.amplitude_envelope == self.threshold] = 0

        end_time = n_samples / self._wav_obj.getframerate()
        self.times = np.linspace(
            0,
            end_time,
            num=len(self.amplitude_envelope),
        )

    @property
    def time_spent_barking(self) -> float:
        """Give the time the dog spend barking based on sound intensity.

        Barking is any point in `self.amplitude_envelope` where the signal is above 0.
        Take into account that the signal was thresholed in the init so that where the
        envelope was under `self.threshold` the signal is set to 0.

        :return: the time spent barking in seconds
        """
        loud_noise = self.amplitude_envelope[self.amplitude_envelope > 0]
        samples = len(loud_noise) * self._step
        return samples / self._wav_obj.getframerate()

    @property
    def bark_times(self) -> np.ndarray:
        return self.times[self.amplitude_envelope > 0]

    def __str__(self) -> str:
        return (
            "File: "
            + self.file_name
            + "\ntime barking: "
            + str(datetime.timedelta(seconds=self.time_spent_barking))
            + "\nbarked at: "
            + str(self.bark_times)
        )
