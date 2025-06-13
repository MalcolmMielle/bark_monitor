from pathlib import Path
from typing import Callable

from bark_monitor.base_sync import BaseSync
from bark_monitor.recorders.base_recorder import BaseRecorder


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
