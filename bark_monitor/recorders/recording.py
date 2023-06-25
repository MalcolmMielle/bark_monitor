from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import jsonpickle

from bark_monitor.google_sync import GoogleSync


class Recording:
    """Class to read and write the recording state.

    The recording state needs to be consistent for the whole app. This is a helper class
    to load and modify that state.
    """

    __create_key = object()

    def __init__(self, create_key, output_folder: str) -> None:
        self._start: Optional[datetime] = None
        self._start_end: list[tuple[datetime, Optional[datetime]]] = []
        self._time_barked: dict[str, timedelta] = {}
        self._output_folder = Path(output_folder).absolute()
        self._activity_tracker: dict[datetime, str] = {}

        assert (
            create_key == Recording.__create_key
        ), "Recording objects must be created using Recording.read"

    @property
    def output_folder(self) -> Path:
        return self._output_folder

    @output_folder.setter
    def output_folder(self, output_folder: Path) -> None:
        self._output_folder = output_folder
        self.save()

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
    def start_end(self) -> list[tuple[datetime, Optional[datetime]]]:
        return self._start_end

    @property
    def all_time_barked(self) -> dict[str, timedelta]:
        return self._time_barked

    @property
    def time_barked(self) -> timedelta:
        now = datetime.now().strftime("%d-%m-%Y")
        return self._time_barked[now]

    def add_time_barked(self, value: timedelta, day: Optional[str] = None) -> None:
        if day is None:
            day = datetime.now().strftime("%d-%m-%Y")
        if day not in self._time_barked:
            self._time_barked[day] = timedelta(0)
        timedelta(0)
        self._time_barked[day] = self._time_barked[day] + value
        self.save()

    @property
    def start(self) -> Optional[datetime]:
        return self._start

    @start.setter
    def start(self, value: datetime) -> None:
        self._start = value
        self.save()

    def end(self, value: datetime) -> None:
        assert self._start is not None
        self._start_end.append((self._start, value))
        self._start = None
        self.save()

    @property
    def _path(self) -> Path:
        return Path(self.output_folder, "recording.json")

    def save(self):
        encoded = jsonpickle.encode(self, keys=True)
        assert encoded is not None
        with open(str(self._path), "w") as outfile:
            outfile.write(encoded)

    def save_to_google(self):
        GoogleSync.update_file(self._path)

    def merge(self, recording: "Recording") -> None:
        for el in recording.start_end:
            if el not in self.start_end:
                self.start_end.append(el)
        self._activity_tracker = recording.activity_tracker | self._activity_tracker
        self._time_barked = recording.all_time_barked | self._time_barked

    @classmethod
    def read(cls, output_folder: str) -> "Recording":
        """Factory method to load the state.

        The state is loaded and written from/to `output_folder`.

        :return: the state in `output_folder`
        """
        state = Recording(cls.__create_key, output_folder)
        if state._path.exists():
            with open(state._path, "r") as file:
                lines = file.read()
                state: "Recording" = jsonpickle.decode(lines, keys=True)  # type: ignore

        past_state_bytes = GoogleSync.load_state()
        if past_state_bytes is not None:
            old_state: "Recording" = jsonpickle.decode(
                past_state_bytes, keys=True
            )  # type: ignore
            state.merge(old_state)

        return state
