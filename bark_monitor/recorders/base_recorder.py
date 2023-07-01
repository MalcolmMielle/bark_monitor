import logging
import threading
import wave
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional

import pyaudio

from bark_monitor.google_sync import GoogleSync
from bark_monitor.recorders.recording import Recording
from bark_monitor.very_bark_bot import VeryBarkBot


class BaseRecorder(ABC):
    _chat_bot: VeryBarkBot

    def __init__(
        self,
        output_folder: str,
        framerate: int = 44100,
        chunk: int = 4096,
    ) -> None:
        self.running = False
        self.is_paused = False

        self._chunk = chunk  # Record in chunks of 1024 samples
        self._sample_format = pyaudio.paInt16  # 16 bits per sample
        self._channels = 1
        self._fs = framerate

        self._frames = []  # Initialize array to store frames

        self._t: Optional[threading.Thread] = None

        self._pyaudio_interface: Optional[pyaudio.PyAudio] = None
        self._stream: Optional[pyaudio.Stream] = None

        self._bark_logger = logging.getLogger("bark_monitor")

        self.output_folder = output_folder

        self._bark_logger.info("Starting bot")

    def start_bot(self, bot: VeryBarkBot) -> None:
        self._chat_bot = bot
        self._chat_bot.start(self)

    @property
    def audio_folder(self) -> Path:
        return Path(self.output_folder, "audio")

    @property
    def _filename(self) -> Path:
        now = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        filename = Path(
            self.audio_folder,
            datetime.now().strftime("%d-%m-%Y"),
            now + ".wav",
        )
        if not filename.parent.exists():
            filename.parent.mkdir(parents=True)
        return filename.absolute()

    def _init(self):
        recording = Recording.read(self.output_folder)
        recording.start = datetime.now()
        self.running = True

    def record(self) -> None:
        self._init()
        self._record()

    def stop(self) -> None:
        self.running = False
        recording = Recording.read(self.output_folder)
        recording.end(datetime.now())

        # Sync with google
        recording.save_to_google()
        GoogleSync.save_audio(str(self.audio_folder))

        self._stop()

    def _stop(self) -> None:
        if self._t is None:
            return
        self._t.join()

    def _save_recording(
        self, frames: list[bytes], filename: Optional[Path] = None
    ) -> Path:
        """Save a recording of `frames` to `filename`.

        If `filename` is None, it defaults to the config location with a datetime.

        :return: the path at which the recording is saved.
        """
        if filename is None:
            filename = self._filename
        # Save the recorded data as a WAV file
        assert self._pyaudio_interface is not None
        wf = wave.open(str(filename), "wb")
        wf.setnchannels(self._channels)
        wf.setsampwidth(self._pyaudio_interface.get_sample_size(self._sample_format))
        wf.setframerate(self._fs)
        wf.writeframes(b"".join(frames))
        wf.close()
        return filename

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

    def _record(self) -> None:
        self._t = threading.Thread(target=self._record_loop)
        self._t.start()

    @abstractmethod
    def _record_loop(self) -> None:
        raise NotImplementedError("abstract")
