import threading
import wave

import pyaudio
from pynput import keyboard

from dog_bark.bark_reaction import BarkReaction


class Recorder:
    _pyaudio: pyaudio.PyAudio
    _stream: pyaudio.Stream

    def __init__(self, filename: str, bark_level: int = 20000) -> None:
        self._chunk = 1024  # Record in chunks of 1024 samples
        self._sample_format = pyaudio.paInt16  # 16 bits per sample
        self._channels = 1
        self._fs = 44100
        self._filename = filename

        self._frames = []  # Initialize array to store frames
        self._running = False

        self._bark_reaction = BarkReaction(bark_level)

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
        # create thread with function `loading`
        self.t = threading.Thread(target=self.record_sound)
        # start thread
        self.t.start()
        print("Recording started")
        with keyboard.Listener(on_release=self.on_release) as listener:  # type: ignore
            listener.join()

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

    def record_sound(self):
        while self._running:
            data = self._stream.read(self._chunk)
            self._frames.append(data)

            self._bark_reaction.react(data)

    def on_release(self, key):
        if key == keyboard.Key.esc:
            # stop listener
            self._running = False
            self.t.join()
            print("Stopped recording")
            return False
