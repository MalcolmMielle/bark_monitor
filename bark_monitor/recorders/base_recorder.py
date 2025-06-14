import logging
import threading
import wave
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Callable

import pyaudio

from bark_monitor.google_sync import BaseSync
from bark_monitor.recorders.recording import Recording


class BaseRecorder(ABC):
    def __init__(
        self,
        sync: BaseSync,
        output_folder: Path,
        framerate: int = 44100,
        chunk: int = 4096,
        send_text_callback: Callable[[str], None] | None = None,
    ) -> None:
        self.running = False
        self.is_paused = False

        self._chunk = chunk  # Record in chunks of 1024 samples
        self._sample_format = pyaudio.paInt16  # 16 bits per sample
        self._channels = 1
        self._fs = framerate

        self._frames: list[bytes] = []  # Initialize array to store frames

        self._t: threading.Thread | None = None

        self._pyaudio_interface: pyaudio.PyAudio | None = None
        self._stream: pyaudio.Stream | None = None

        self._bark_logger = logging.getLogger("bark_monitor")

        self.output_folder = output_folder

        self._bark_logger.info("Starting bot")
        self._sync = sync

        self.send_text_callback = send_text_callback

    @property
    def sync(self) -> BaseSync:
        return self._sync

    @property
    def audio_folder(self) -> Path:
        audio_path = Path(self.output_folder, "audio")
        if not audio_path.exists():
            audio_path.mkdir(parents=True)
        return audio_path

    @property
    def today_audio_folder(self) -> Path:
        return Path(
            self.audio_folder,
            datetime.now().strftime("%d-%m-%Y"),
        )

    @property
    def _filename(self) -> Path:
        now = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        filename = Path(
            self.today_audio_folder,
            now + ".wav",
        )
        if not filename.parent.exists():
            filename.parent.mkdir(parents=True)
        return filename.absolute()

    def _init(self):
        recording = Recording.read(self.output_folder, sync_service=self._sync)
        recording.start = datetime.now()
        self.running = True

    def record(self) -> None:
        self._init()
        self._record()

    def stop(self) -> None:
        self.running = False
        recording = Recording.read(self.output_folder, sync_service=self._sync)
        recording.end(datetime.now())

        # Sync
        recording.upload(self._sync)
        self._sync.save_audio(self.audio_folder)

        self._stop()

    def _stop(self) -> None:
        if self._t is None:
            return
        self._t.join()

    def _save_recording(self, frames: list[bytes], prefix: str | None = None) -> Path:
        """Save a recording of `frames` to `self._filename`.

        :return: the path at which the recording is saved.
        """
        filepath = self._filename
        if prefix is not None:
            filepath = Path(self.today_audio_folder, prefix + " " + self._filename.name)
        file = self._save_recording_to(frames, filepath)
        if self.send_text_callback is not None:
            self.send_text_callback(
                "Save file: "
                + str(filepath)
                + ".\nDownload it with \n\n ```\n/audio "
                + filepath.name
                + "\n```"
            )
        return file

    def _save_recording_to(self, frames: list[bytes], filepath: Path) -> Path:
        """Save a recording of `frames` to `filepath`.

        :return: the path at which the recording is saved.
        """
        # Save the recorded data as a WAV file
        assert self._pyaudio_interface is not None
        wf = wave.open(str(filepath), "wb")
        wf.setnchannels(self._channels)
        wf.setsampwidth(self._pyaudio_interface.get_sample_size(self._sample_format))
        wf.setframerate(self._fs)
        wf.writeframes(b"".join(frames))
        wf.close()
        return filepath

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
