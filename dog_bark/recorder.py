import threading
import wave
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pyaudio


class Recorder:
    _pyaudio: pyaudio.PyAudio
    _stream: pyaudio.Stream

    def __init__(self, filename: str, bark_level: int, bark_func) -> None:
        self._chunk = 1024  # Record in chunks of 1024 samples
        self._sample_format = pyaudio.paInt16  # 16 bits per sample
        self._channels = 1
        self._fs = 44100
        self.filename = filename

        self._frames = []  # Initialize array to store frames
        self._running = False

        self._bark_level = bark_level

        self.is_paused = False
        self.bark_func = bark_func

        self._pyaudio = pyaudio.PyAudio()  # Create an interface to PortAudio
        self._stream = self._pyaudio.open(
            format=self._sample_format,
            channels=self._channels,
            rate=self._fs,
            frames_per_buffer=self._chunk,
            input=True,
        )

        self._t: Optional[threading.Thread] = None

        self._last_bark = datetime.now()

    def stop(self):
        self._running = False

    def clear(self):
        # Stop and close the stream
        self._stream.stop_stream()
        self._stream.close()
        # Terminate the PortAudio interface
        self._pyaudio.terminate()

        print("Finished recording")

        # Save the recorded data as a WAV file
        wf = wave.open(self.filename, "wb")
        wf.setnchannels(self._channels)
        wf.setsampwidth(self._pyaudio.get_sample_size(self._sample_format))
        wf.setframerate(self._fs)
        wf.writeframes(b"".join(self._frames))
        wf.close()

    def _is_bark(self, signal: bytes):
        np_data = np.frombuffer(signal, dtype=np.int16)
        max_val = np.amax(np_data)
        if max_val >= self._bark_level:
            return True
        return False

    def record_thread(self):
        self._t = threading.Thread(target=self.record)
        self._t.start()

    def stop_thread(self):
        if self._t is None:
            return
        self.stop()
        self._t.join()

    def record(self):
        self._running = True
        print("Recording started")
        while self._running:
            if not self.is_paused:
                data = self._stream.read(self._chunk)
                self._frames.append(data)
                if self._is_bark(data) and (
                    datetime.now() - self._last_bark > timedelta(seconds=1)
                ):
                    self.bark_func()
            else:
                print("is paused")
        self.clear()
