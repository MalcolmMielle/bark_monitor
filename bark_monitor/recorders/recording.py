import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import jsonpickle
import pandas as pd


class Recording:
    __create_key = object()

    def __init__(self, create_key, output_folder: str) -> None:
        self._start: Optional[str] = None
        self._start_end: list[tuple[str, Optional[str]]] = []
        self._time_barked = pd.Timedelta(0).isoformat()
        self._output_folder = Path(output_folder).absolute()

        assert (
            create_key == Recording.__create_key
        ), "Recording objects must be created using Recording.read"

    @property
    def start_end(self) -> list[tuple[str, Optional[str]]]:
        return self._start_end

    @property
    def time_barked(self) -> timedelta:
        return pd.Timedelta(self._time_barked).to_pytimedelta()

    @time_barked.setter
    def time_barked(self, value: timedelta) -> None:
        timedelta_pd = pd.Timedelta(value)
        self._time_barked = (pd.Timedelta(self._time_barked) + timedelta_pd).isoformat()
        self.save()

    @property
    def start(self) -> Optional[str]:
        return self._start

    @start.setter
    def start(self, value: datetime) -> None:
        self._start = value.time().isoformat()
        self.save()

    def end(self, value: datetime) -> None:
        assert self._start is not None
        self._start_end.append((self._start, value.time().isoformat()))
        self._start = None
        self.save()

    @staticmethod
    def folder(output_folder: Path) -> Path:
        now = datetime.now().strftime("%d-%m-%Y")
        folder = Path(output_folder, now)
        if not folder.exists():
            folder.mkdir()
        return folder

    @property
    def _path(self) -> str:
        return str(Path(Recording.folder(self._output_folder), "recording.json"))

    def save(self):
        encoded = jsonpickle.encode(self)
        assert encoded is not None
        with open(self._path, "w") as outfile:
            outfile.write(encoded)

    @classmethod
    def read(cls, output_folder: str) -> "Recording":
        state = Recording(cls.__create_key, output_folder)
        try:
            with open(state._path, "r") as file:
                lines = file.read()
                state = jsonpickle.decode(lines)
                return state
        except FileNotFoundError:
            return state
