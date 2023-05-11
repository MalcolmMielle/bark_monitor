import logging
import threading
import wave
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Optional

import numpy as np
import pyaudio

from bark_monitor.recorders.recording import Recording


class Recorder:
    def __init__(
        self,
        output_folder: str,
        bark_func: Optional[list[Callable[[int], None]]] = None,
        stop_bark_func: Optional[list[Callable[[timedelta], None]]] = None,
    ) -> None:
        self._bark_level: int = 0

        if bark_func is None:
            bark_func = []
        self.bark_func = bark_func

        if stop_bark_func is None:
            stop_bark_func = []
        self.stop_bark_func = stop_bark_func

        self._barking_at = datetime.now()
        self._is_barking = False
        self.running = False
        self.is_paused = False

        self._chunk = 1024  # Record in chunks of 1024 samples
        self._sample_format = pyaudio.paInt16  # 16 bits per sample
        self._channels = 1
        self._fs = 44100

        self._frames = []  # Initialize array to store frames

        self._t: Optional[threading.Thread] = None

        self._last_bark = datetime.now()
        self.total_time_barking = timedelta(seconds=0)

        self._pyaudio_interface: Optional[pyaudio.PyAudio] = None
        self._stream: Optional[pyaudio.Stream] = None

        self._bark_logger = logging.getLogger("bark_monitor")

        self._output_folder = output_folder

    @property
    def bark_level(self) -> Optional[int]:
        return self._bark_level

    @property
    def _filename(self) -> str:
        now = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        filename = str(Path(Recording.folder(self._output_folder), now + ".wav"))
        if not Path(filename).parent.exists():
            Path(filename).parent.mkdir()
        return filename

    def _init(self):
        self._barking_at = datetime.now()
        self._is_barking = False
        recording = Recording.read(self._output_folder)
        recording.start = datetime.now()
        self.running = True

    def record(self):
        self._init()
        self._record()

    def stop(self):
        self.running = False
        recording = Recording.read(self._output_folder)
        recording.time_barked = self.total_time_barking
        recording.end(datetime.now())
        self._bark_level = 0
        self._stop()

    def _is_bark(self, value: int) -> bool:
        if self._bark_level == 0:
            return False
        return value >= self._bark_level

    def _save_recording(self) -> None:
        # Save the recorded data as a WAV file
        assert self._pyaudio_interface is not None
        wf = wave.open(self._filename, "wb")
        wf.setnchannels(self._channels)
        wf.setsampwidth(self._pyaudio_interface.get_sample_size(self._sample_format))
        wf.setframerate(self._fs)
        wf.writeframes(b"".join(self._frames))
        wf.close()

    def _signal_to_intensity(self, signal: bytes) -> int:
        np_data = np.frombuffer(signal, dtype=np.int16)
        return np.amax(np_data)  # type: ignore

    def _record(self) -> None:
        self._t = threading.Thread(target=self._record_loop)
        self._t.start()

    def _stop(self) -> None:
        if self._t is None:
            return
        self._t.join()

    def _start_stream(self) -> None:
        self._pyaudio_interface = pyaudio.PyAudio()  # Create an interface to PortAudio
        self._stream = self._pyaudio_interface.open(
            format=self._sample_format,
            channels=self._channels,
            rate=self._fs,
            frames_per_buffer=self._chunk,
            input=True,
        )

    def _stop_stream(self) -> None:
        if self._stream is not None:
            # Stop and close the stream
            self._stream.stop_stream()
            self._stream.close()

        if self._pyaudio_interface is not None:
            # Terminate the PortAudio interface
            self._pyaudio_interface.terminate()

    def _set_bark_level(self, range_measurements: int = 100) -> None:
        assert self._stream is not None
        self._bark_level = 0
        for _ in range(range_measurements):
            data = self._stream.read(self._chunk)
            self._bark_level = max(self._bark_level, self._signal_to_intensity(data))
        self._bark_level *= 2

    def _record_loop(self) -> None:
        self._start_stream()
        self._bark_logger.info("Recording started")

        assert self._stream is not None
        self._set_bark_level()

        while self.running:
            if self.is_paused:
                continue

            data = self._stream.read(self._chunk)
            intensity = self._signal_to_intensity(data)

            # Save data if dog is barking
            is_bark = self._is_bark(intensity)
            if is_bark:
                self._frames.append(data)

            # If to update time and stop recording the bark
            if is_bark:
                self._barking_at = datetime.now()
                if not self._is_barking:
                    self._is_barking = True
                    for func in self.bark_func:
                        func(intensity - self._bark_level)
            elif self._is_barking and (datetime.now() - self._barking_at) > timedelta(
                seconds=5
            ):
                barked_for = timedelta(len(self._frames) / self._fs)
                assert self._barking_at is not None
                self._is_barking = False
                self.total_time_barking = self.total_time_barking + barked_for

                for func in self.stop_bark_func:
                    func(barked_for)
                self._save_recording()
                self._frames = []

        self._stop_stream()
