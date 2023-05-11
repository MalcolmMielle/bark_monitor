from pathlib import Path

import jsonpickle
from telegram import Chat


class Chats:
    __create_key = object()

    def __init__(self, create_key, config_folder: str) -> None:
        self._chats: set[int] = set()
        self._config_folder = Path(config_folder).absolute()

        assert (
            create_key == Chats.__create_key
        ), "Recording objects must be created using Recording.read"

    @property
    def chats(self) -> set[int]:
        return self._chats

    def add(self, chat: Chat) -> None:
        # Comment to not add new users to the bot
        self._chats.add(chat.id)
        self.save()

    @staticmethod
    def folder(config_folder: Path) -> Path:
        if not config_folder.exists():
            config_folder.mkdir()
        return config_folder

    @property
    def _path(self) -> str:
        return str(Path(Chats.folder(self._config_folder), "chats.json"))

    def save(self):
        # Using a JSON string
        encoded = jsonpickle.encode(self)
        assert encoded is not None
        with open(self._path, "w") as outfile:
            outfile.write(encoded)

    @classmethod
    def read(cls, config_folder: str) -> "Chats":
        state = Chats(cls.__create_key, config_folder)
        try:
            with open(state._path, "r") as file:
                # dict = json.load(file)
                lines = file.read()
                state = jsonpickle.decode(lines)
                return state
        except FileNotFoundError:
            return state
