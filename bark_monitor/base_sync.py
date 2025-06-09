import abc
from pathlib import Path


class BaseSync(abc.ABC):
    @staticmethod
    @abc.abstractmethod
    def update_file(file_path: Path) -> None:
        raise NotImplementedError("update_file not implemented")

    @staticmethod
    @abc.abstractmethod
    def save_audio(audio_folder: str) -> None:
        raise NotImplementedError("save_audio not implemented")

    @staticmethod
    @abc.abstractmethod
    def load_state() -> bytes | None:
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
