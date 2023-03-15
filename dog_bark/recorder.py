import threading
import wave

import numpy as np
import pyaudio

from dog_bark.very_bark_bot import VeryBarkBot


class Recorder:
    _pyaudio: pyaudio.PyAudio
    _stream: pyaudio.Stream

    def __init__(self, filename: str, bark_level: int) -> None:
        self._chunk = 1024  # Record in chunks of 1024 samples
        self._sample_format = pyaudio.paInt16  # 16 bits per sample
        self._channels = 1
        self._fs = 44100
        self._filename = filename

        self._frames = []  # Initialize array to store frames
        self._running = False

        self._bark_level = bark_level
        self._bot = VeryBarkBot()

    def __enter__(self):
        self._pyaudio = pyaudio.PyAudio()  # Create an interface to PortAudio
        self._stream = self._pyaudio.open(
            format=self._sample_format,
            channels=self._channels,
            rate=self._fs,
            frames_per_buffer=self._chunk,
            input=True,
        )
        return self

    def record(self):
        self._running = True
        self._t = threading.Thread(target=self.record_sound)
        self._t.start()
        print("Recording started")
        self._bot.init()

        self._running = False
        self._t.join()

    def __exit__(self, exc_type, exc_value, exc_tb):
        # Stop and close the stream
        self._stream.stop_stream()
        self._stream.close()
        # Terminate the PortAudio interface
        self._pyaudio.terminate()

        print("Finished recording")

        # Save the recorded data as a WAV file
        wf = wave.open(self._filename, "wb")
        wf.setnchannels(self._channels)
        wf.setsampwidth(self._pyaudio.get_sample_size(self._sample_format))
        wf.setframerate(self._fs)
        wf.writeframes(b"".join(self._frames))
        wf.close()

    def _is_bark(self, signal: bytes):
        np_data = np.frombuffer(signal, dtype=np.int16)
        max_val = np.amax(np_data)
        print(max_val)
        if max_val >= self._bark_level:
            return True
        return False

    def record_sound(self):
        while self._running:
            data = self._stream.read(self._chunk)
            self._frames.append(data)
            if self._is_bark(data):
                self._bot.send_bark()
