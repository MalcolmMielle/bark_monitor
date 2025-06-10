import abc
import shutil
from pathlib import Path


class BaseSync(abc.ABC):
    @abc.abstractmethod
    def update_file(self, file_path: Path) -> None:
        raise NotImplementedError("update_file not implemented")

    def save_audio(self, audio_folder: Path) -> None:
        shutil.make_archive("bark_monitor_audio", "zip", audio_folder)
        self.update_file(Path("bark_monitor_audio.zip"))

    @abc.abstractmethod
    def load_state(self) -> bytes | None:
        """Load the recording state stored in the "recording.json" file"""
        raise NotImplementedError("load_state not implemented")

    @abc.abstractmethod
    def status(self) -> str:
        raise NotImplementedError("get_status not implemented")

    @abc.abstractmethod
    def login(self) -> tuple[bool, str]:
        raise NotImplementedError("login not implemented")

    @abc.abstractmethod
    def login_step_2(self, text: str) -> None:
        raise NotImplementedError("login_step_2 not implemented")
