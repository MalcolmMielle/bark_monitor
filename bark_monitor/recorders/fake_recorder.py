from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable

from bark_monitor.base_sync import BaseSync
from bark_monitor.recorders.base_recorder import BaseRecorder
from bark_monitor.recorders.recording import Activity, Recording


class FakeRecorder(BaseRecorder):
    def __init__(
        self,
        sync: BaseSync,
        output_folder: Path,
        framerate: int = 44100,
        chunk: int = 4096,
        send_text_callback: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(sync, output_folder, framerate, chunk, send_text_callback)

    def _record_loop(self) -> None:
        pass

    def record(self) -> None:
        self.running = True

    def stop(self) -> None:
        self.running = False

    def add_bark(self) -> None:
        # increase time barked in state
        recording = Recording.read(
            output_folder=self.output_folder, sync_service=self._sync
        )
        recording.add_activity(
            Activity(
                label="Fake Bark",
                date=datetime.now(),
                duration=timedelta(seconds=1),
                audio_path=Path("fake_audio.wav"),
            ),
        )
        if self.send_text_callback is not None:
            self.send_text_callback("Fake Bark")
