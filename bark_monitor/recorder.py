import threading
import wave
from datetime import datetime, timedelta
from typing import Callable, Optional

import numpy as np
import pyaudio


class Recorder:
    _pyaudio: pyaudio.PyAudio
    _stream: pyaudio.Stream

    def __init__(
        self,
        filename: str,
        bark_level: int,
        bark_func: Callable[[int], None],
        stop_bark_func: Callable[[timedelta], None],
    ) -> None:
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
        self.stop_bark_func = stop_bark_func

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
        self.total_time_barking = timedelta(seconds=0)

    def stop(self) -> None:
        self._running = False

    def clear(self) -> None:
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

    def record(self) -> None:
        self._running = True
        print("Recording started")

        barking_start: Optional[datetime] = None
        is_barking = False

        while self._running:
            if not self.is_paused:
                data = self._stream.read(self._chunk)
                self._frames.append(data)
                is_bark, intensity = self._is_bark(data)
                print(intensity)

                # Those two ifs are separated because we also want to trigger when
                # barking occurs after we have flagged it to only go out when the
                # barking stops
                if is_bark:
                    if not is_barking:
                        is_barking = True
                        self.bark_func(intensity)
                        barking_start = datetime.now()
                elif is_barking:
                    is_barking = False
                    assert barking_start is not None
                    self.total_time_barking = self.total_time_barking + (
                        datetime.now() - barking_start
                    )
                    self.stop_bark_func(datetime.now() - barking_start)
                    barking_start = None
        self.clear()
