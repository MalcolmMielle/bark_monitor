import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd


class Recording:
    __create_key = object()

    def __init__(self, create_key) -> None:
        self._start: Optional[str] = None
        self._start_end: list[tuple[str, Optional[str]]] = []
        self._time_barked = pd.Timedelta(0).isoformat()

        assert (
            create_key == Recording.__create_key
        ), "Recording objects must be created using Recording.read"

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
    def folder() -> str:
        now = datetime.now().strftime("%d-%m-%Y")
        folder = str(Path("recordings", now))
        if not Path(folder).exists():
            Path(folder).mkdir()
        return folder

    @property
    def _path(self) -> str:
        return str(Path(Recording.folder(), "recording.json"))

    def save(self):
        json_string = json.dumps(
            self, default=lambda o: o.__dict__, sort_keys=True, indent=4
        )
        # Using a JSON string
        with open(self._path, "w") as outfile:
            outfile.write(json_string)

    @classmethod
    def read(cls) -> "Recording":
        state = Recording(cls.__create_key)
        try:
            with open(state._path, "r") as file:
                dict = json.load(file)
                state.__dict__ = dict
                return state
        except FileNotFoundError:
            return state
