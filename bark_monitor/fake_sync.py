from pathlib import Path

from bark_monitor.base_sync import BaseSync


class FakeSync(BaseSync):
    def update_file(self, file_path: Path) -> None:
        pass

    def load_state(self) -> bytes | None:
        """Load the recording state stored in the "recording.json" file"""
        pass

    def status(self) -> str:
        "Not connected"

    def login(self) -> tuple[bool, str]:
        raise NotImplementedError("login not implemented")

    def login_step_2(self, text: str) -> None:
        raise NotImplementedError("login_step_2 not implemented")
