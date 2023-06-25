import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest import mock

import jsonpickle

from bark_monitor.recorders.recording import Recording


class TestRecording(unittest.TestCase):
    def test_goal(self) -> None:
        recording = Recording.read("tests/data")
        self.assertEqual(recording.time_barked, timedelta(23))
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
        recording = Recording.read("tests/data")
        recording.output_folder = Path("tests/data")
        recording.clear_activity()
        self.assertEqual(len(recording.activity_tracker), 0)

        recording = Recording.read("tests/data")
        self.assertEqual(len(recording.activity_tracker), 0)
        time = datetime(year=2023, month=1, day=1)
        recording.add_activity(time, "test activity")
        key = list(recording.activity_tracker.keys())[0]
        self.assertEqual(key, time)

        recording = Recording.read("tests/data")
        key = list(recording.activity_tracker.keys())[0]
        self.assertEqual(key, time)

        time = datetime(year=2023, month=1, day=2)
        recording.add_activity(time, "test activity")
        self.assertEqual(len(recording.activity_tracker), 2)

        recording = Recording.read("tests/data")
        self.assertEqual(len(recording.activity_tracker), 2)

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
