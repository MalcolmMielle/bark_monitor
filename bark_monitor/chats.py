import json
from pathlib import Path

import jsonpickle
from telegram import Chat


class Chats:
    __create_key = object()

    def __init__(self, create_key) -> None:
        self._chats: set[int] = set()

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
    def folder() -> str:
        folder = str(Path("config"))
        if not Path(folder).exists():
            Path(folder).mkdir()
        return folder

    @property
    def _path(self) -> str:
        return str(Path(Chats.folder(), "chats.json"))

    def save(self):
        # Using a JSON string
        encoded = jsonpickle.encode(self)
        assert encoded is not None
        with open(self._path, "w") as outfile:
            outfile.write(encoded)

    @classmethod
    def read(cls) -> "Chats":
        state = Chats(cls.__create_key)
        try:
            with open(state._path, "r") as file:
                # dict = json.load(file)
                lines = file.read()
                state = jsonpickle.decode(lines)
                return state
        except FileNotFoundError:
            return state
