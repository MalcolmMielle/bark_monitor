from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import jsonpickle
from fastapi_rss import Category, CategoryAttrs, Item

from bark_monitor.google_sync import BaseSync


@dataclass(kw_only=True)
class Activity:
    label: str
    date: datetime
    duration: timedelta
    audio_path: Path

    def to_rss_feed_item(self) -> Item:
        return Item(
            title="I barked: " + self.label,
            description="This happened on "
            + self.date.isoformat()
            + " for "
            + str(self.duration.seconds)
            + " seconds. Download the recording at the link",
            author="Your dog",
            link=str(self.audio_path),
        )


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
        self._output_folder = Path(output_folder).absolute()

        self._activity_tracker: deque[Activity] = deque()
        """Sorted (based on date) list of activity"""

        assert create_key == Recording.__create_key, (
            "Recording objects must be created using Recording.read"
        )

    @property
    def last_label(self) -> Activity | None:
        return self._last_label

    @property
    def output_folder(self) -> Path:
        return self._output_folder

    @output_folder.setter
    def output_folder(self, output_folder: Path) -> None:
        self._output_folder = output_folder
        self.save()

    def daily_activities_formated(self) -> str:
        activities = ""
        for activity in self.activity_tracker:
            if activity.date.date() == datetime.today().date():
                activities += (
                    activity.date.strftime("%H %M %S") + ": " + activity.label + "\n"
                )
        return activities

    def activities_formated(self) -> str:
        activities = ""
        for activity in self.activity_tracker:
            activities += activity.date.isoformat() + "---" + activity.label + "\n"
        return activities[:-1]

    @property
    def activity_tracker(self) -> deque[Activity]:
        return self._activity_tracker

    def add_activity(self, activity: Activity) -> None:
        self._activity_tracker.appendleft(activity)
        self._last_label = activity
        self.save()

    def clear_activity(self) -> None:
        self._activity_tracker = deque()
        self._last_label = None
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
        self._activity_tracker = recording.activity_tracker + self._activity_tracker
        self._activity_tracker = deque(
            sorted(
                self._activity_tracker, key=lambda activity: activity.date, reverse=True
            )
        )

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

    @property
    def feed_data(self) -> dict[str, Any]:
        items = []
        for activity in self._activity_tracker:
            print("Date", activity.date.isoformat())
            items.append(activity.to_rss_feed_item())
        return {
            "title": "Bark monitor",
            "link": "http://www.bark.malcolmmielle.phd/",
            "description": "Is watson barking.",
            "language": "en-us",
            # "copyright": "Copyright 1997-2002 Dave Winer",
            # "last_build_date": datetime.datetime(2002, 9, 30, 11, 0, 0),
            # "docs": "http://backend.userland.com/rss",
            "generator": "Bark Monitor Watson",
            "category": [
                Category(content="1765", attrs=CategoryAttrs(domain="Syndic8"))
            ],
            "managing_editor": "barkmonitor@malcolmmielle.phd",
            "webmaster": "barkmonitor@malcolmmielle.phd",
            "ttl": 40,
            "item": items,
        }
