from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import jsonpickle
import pandas as pd


class Recording:
    """Class to read and write the recording state.

    The recording state needs to be consistent for the whole app. This is a helper class
    to load and modify that state.
    """

    __create_key = object()

    def __init__(self, create_key, output_folder: str) -> None:
        self._start: Optional[str] = None
        self._start_end: list[tuple[str, Optional[str]]] = []
        self._time_barked = timedelta(0)
        self._output_folder = Path(output_folder).absolute()
        self._activity_tracker: dict[datetime, str] = {}

        assert (
            create_key == Recording.__create_key
        ), "Recording objects must be created using Recording.read"

    @property
    def activity_tracker(self) -> dict[datetime, str]:
        return self._activity_tracker

    def add_activity(self, time: datetime, activity: str) -> None:
        self._activity_tracker[time] = activity
        self.save()

    def clear_activity(self) -> None:
        self._activity_tracker = {}
        self.save()

    @property
    def start_end(self) -> list[tuple[str, Optional[str]]]:
        return self._start_end

    @property
    def time_barked(self) -> timedelta:
        return self._time_barked

    def add_time_barked(self, value: timedelta) -> None:
        self._time_barked = self._time_barked + value
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
            folder.mkdir(parents=True)
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
        """Factory method to load the state.

        The state is loaded and written from/to `output_folder`.

        :return: the state in `output_folder`
        """
        state = Recording(cls.__create_key, output_folder)
        try:
            with open(state._path, "r") as file:
                lines = file.read()
                state: "Recording" = jsonpickle.decode(lines)
                # Here to convert old format of recording if needed
                if type(state._time_barked) == str:
                    state._time_barked = pd.Timedelta(
                        state._time_barked
                    ).to_pytimedelta()
                return state  # type: ignore
        except FileNotFoundError:
            return state
