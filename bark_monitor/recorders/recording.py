from datetime import datetime, timedelta
from pathlib import Path

import jsonpickle

from bark_monitor.google_sync import BaseSync


class Recording:
    """Class to read and write the recording state.

    The recording state needs to be consistent for the whole app. This is a helper class
    to load and modify that state.
    """

    __create_key = object()

    def __init__(self, create_key, output_folder: Path) -> None:
        self._start: datetime | None = None
        self._start_end: list[tuple[datetime, datetime | None]] = []
        self._time_barked: dict[str, timedelta] = {}
        self._time_barked["today"] = timedelta()
        self._output_folder = Path(output_folder).absolute()
        self._activity_tracker: dict[datetime, str] = {}

        assert create_key == Recording.__create_key, (
            "Recording objects must be created using Recording.read"
        )

    @property
    def output_folder(self) -> Path:
        return self._output_folder

    @output_folder.setter
    def output_folder(self, output_folder: Path) -> None:
        self._output_folder = output_folder
        self.save()

    def daily_activities_formated(self) -> str:
        activities = ""
        for a_datetime, activity in self.activity_tracker.items():
            if a_datetime.date() == datetime.today().date():
                activities += a_datetime.strftime("%H %M %S") + ": " + activity + "\n"
        return activities

    def activities_formated(self) -> str:
        activities = ""
        for a_datetime, activity in self.activity_tracker.items():
            activities += a_datetime.isoformat() + "---" + activity + "\n"
        return activities[:-1]

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
    def start_end(self) -> list[tuple[datetime, datetime | None]]:
        return self._start_end

    @property
    def all_time_barked(self) -> dict[str, timedelta]:
        return self._time_barked

    @property
    def time_barked(self) -> timedelta:
        now = datetime.now().strftime("%d-%m-%Y")
        if now not in self._time_barked:
            return timedelta(0)
        return self._time_barked[now]

    def add_time_barked(self, value: timedelta, day: str | None = None) -> None:
        if day is None:
            day = datetime.now().strftime("%d-%m-%Y")
        if day not in self._time_barked:
            self._time_barked[day] = timedelta(0)
        timedelta(0)
        self._time_barked[day] = self._time_barked[day] + value
        self.save()

    @property
    def start(self) -> datetime | None:
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
        if not self.output_folder.exists():
            self.output_folder.mkdir(parents=True, exist_ok=True)
        with self._path.open(mode="w") as outfile:
            outfile.write(encoded)

    def upload(self, sync_service: BaseSync) -> None:
        sync_service.update_file(self._path)

    def merge(self, recording: "Recording") -> None:
        for el in recording.start_end:
            if el not in self.start_end:
                self.start_end.append(el)
        self._activity_tracker = recording.activity_tracker | self._activity_tracker
        self._time_barked = recording.all_time_barked | self._time_barked

    @classmethod
    def read(cls, output_folder: Path, sync_service: BaseSync) -> "Recording":
        """Factory method to load the state.

        The state is loaded and written from/to `output_folder`.

        :return: the state in `output_folder`
        """
        state = Recording(cls.__create_key, output_folder)
        if state._path.exists():
            with state._path.open(mode="r") as file:
                lines = file.read()
                state: "Recording" = jsonpickle.decode(lines, keys=True)  # type: ignore

        past_state_bytes = sync_service.load_state()
        if past_state_bytes is not None:
            old_state: "Recording" = jsonpickle.decode(past_state_bytes, keys=True)  # type: ignore
            state.merge(old_state)

        return state
