import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

import jsonpickle

from bark_monitor.google_sync import GoogleSync
from bark_monitor.recorders.recording import Activity, Recording


class TestRecording(unittest.TestCase):
    def test_goal(self) -> None:
        sync_service = GoogleSync(credential_file=Path(""))
        recording = Recording.read(Path("tests/data"), sync_service=sync_service)
        self.assertEqual(recording._time_barked["today"], timedelta(2))
        self.assertEqual(len(recording.start_end), 1)
        self.assertEqual(
            recording.start_end[0],
            (
                datetime(
                    year=2023,
                    month=6,
                    day=25,
                    hour=18,
                    minute=54,
                    second=35,
                    microsecond=878303,
                ),
                datetime(
                    year=2023,
                    month=6,
                    day=25,
                    hour=18,
                    minute=54,
                    second=40,
                    microsecond=678926,
                ),
            ),
        )

    def test_activity(self) -> None:
        sync_service = GoogleSync(credential_file=Path(""))
        recording = Recording.read(Path("tests/data"), sync_service=sync_service)
        recording.output_folder = Path("tests/data")
        recording.clear_activity()
        self.assertEqual(len(recording.activity_tracker), 0)

        recording = Recording.read(Path("tests/data"), sync_service=sync_service)
        self.assertEqual(len(recording.activity_tracker), 0)
        time = datetime(year=2023, month=1, day=1)
        recording.add_activity(
            Activity(
                date=time,
                label="test activity",
                duration=timedelta(0),
                audio_path=Path(""),
            )
        )
        self.assertEqual(recording.activity_tracker[0].date, time)

        recording = Recording.read(Path("tests/data"), sync_service=sync_service)
        self.assertEqual(recording.activity_tracker[0].date, time)

        time_second = datetime(year=2023, month=1, day=2)
        recording.add_activity(
            Activity(
                date=time_second,
                label="test activity",
                duration=timedelta(0),
                audio_path=Path(""),
            )
        )
        self.assertEqual(len(recording.activity_tracker), 2)
        self.assertEqual(recording.activity_tracker[0].date, time_second)

        recording = Recording.read(Path("tests/data"), sync_service=sync_service)
        self.assertEqual(len(recording.activity_tracker), 2)
        self.assertEqual(recording.activity_tracker[0].date, time_second)
        self.assertEqual(recording.activity_tracker[1].date, time)

    @mock.patch.object(Recording, "save", return_value="None")
    def test_merge(self, _: Recording) -> None:
        with open("tests/data/recording.json", "r") as file:
            lines = file.read()
        state: "Recording" = jsonpickle.decode(lines, keys=True)
        state2: "Recording" = jsonpickle.decode(lines, keys=True)

        state.merge(state2)
        self.assertEqual(len(state.start_end), 1)

        state2.start = datetime.now()
        state2.end(datetime.now())

        state.merge(state2)
        self.assertEqual(len(state.start_end), 2)
