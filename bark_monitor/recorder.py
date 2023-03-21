import threading
import wave
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Optional

import numpy as np
import pyaudio


class Recorder:
    def __init__(
        self,
        bark_level: int,
        bark_func: Callable[[int], None],
        stop_bark_func: Callable[[timedelta], None],
    ) -> None:
        self._chunk = 1024  # Record in chunks of 1024 samples
        self._sample_format = pyaudio.paInt16  # 16 bits per sample
        self._channels = 1
        self._fs = 44100

        self._frames = []  # Initialize array to store frames
        self.running = False

        self._bark_level = bark_level

        self.is_paused = False
        self.bark_func = bark_func
        self.stop_bark_func = stop_bark_func

        self._t: Optional[threading.Thread] = None

        self._last_bark = datetime.now()
        self.total_time_barking = timedelta(seconds=0)

    @staticmethod
    def _filename() -> str:
        now = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        filename = str(Path("recordings", now + ".wav"))
        if not Path(filename).parent.exists():
            Path(filename).parent.mkdir()
        return filename

    def stop(self) -> None:
        self.running = False

    def save_recording(self, sample_width: int) -> None:
        # Save the recorded data as a WAV file
        wf = wave.open(self._filename(), "wb")
        wf.setnchannels(self._channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(self._fs)
        wf.writeframes(b"".join(self._frames))
        wf.close()

    def _is_bark(self, signal: bytes) -> tuple[bool, int]:
        np_data = np.frombuffer(signal, dtype=np.int16)
        max_val = np.amax(np_data)
        if max_val >= self._bark_level:
            return True, max_val
        return False, max_val

    def record_thread(self) -> None:
        self._t = threading.Thread(target=self.record)
        self._t.start()

    def stop_thread(self) -> None:
        if self._t is None:
            return
        self.stop()
        self._t.join()

    def _start_stream(self) -> tuple[pyaudio.PyAudio, pyaudio.Stream]:
        pyaudio_interface = pyaudio.PyAudio()  # Create an interface to PortAudio
        stream = pyaudio_interface.open(
            format=self._sample_format,
            channels=self._channels,
            rate=self._fs,
            frames_per_buffer=self._chunk,
            input=True,
        )
        return pyaudio_interface, stream

    def _stop_stream(
        self, pyaudio_interface: pyaudio.PyAudio, stream: pyaudio.Stream
    ) -> None:
        # Stop and close the stream
        stream.stop_stream()
        stream.close()
        # Terminate the PortAudio interface
        pyaudio_interface.terminate()

    def record(self) -> None:
        pyaudio_interface, stream = self._start_stream()

        self.running = True
        print("Recording started")

        barking_at = datetime.now()
        is_barking = False

        while self.running:
            if self.is_paused:
                continue

            data = stream.read(self._chunk)
            is_bark, intensity = self._is_bark(data)

            # If to check when to record
            if is_bark or (datetime.now() - barking_at) < timedelta(seconds=1):
                self._frames.append(data)

            # If to update time and stop recording the bark
            if is_bark:
                barking_at = datetime.now()
                if not is_barking:
                    is_barking = True
                    self.bark_func(intensity)
            elif is_barking and (datetime.now() - barking_at) > timedelta(seconds=1):
                assert barking_at is not None
                is_barking = False
                self.total_time_barking = self.total_time_barking + (
                    datetime.now() - barking_at
                )
                self.stop_bark_func(datetime.now() - barking_at)
                self.save_recording(
                    pyaudio_interface.get_sample_size(self._sample_format)
                )
                self._frames = []

        self._stop_stream(pyaudio_interface, stream)
