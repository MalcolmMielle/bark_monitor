import datetime
import unittest
from datetime import timedelta
from unittest import mock

from bark_monitor.recorders.recording import Recording


class TestRecording(unittest.TestCase):
    @mock.patch.object(Recording, "folder", return_value="tests/data/")
    def test_goal(self, _: Recording) -> None:
        recording = Recording.read("tests/data")
        self.assertEqual(recording.time_barked, timedelta(2))
        self.assertEqual(len(recording.start_end), 1)
        self.assertEqual(recording.start_end[0], ("19:39:32.163523", "20:04:41.614984"))

    @mock.patch.object(Recording, "folder", return_value="tests/data/")
    def test_activity(self, _: Recording) -> None:
        recording = Recording.read("tests/data")
        recording.clear_activity()
        self.assertEqual(len(recording.activity_tracker), 0)

        recording = Recording.read("tests/data")
        self.assertEqual(len(recording.activity_tracker), 0)
        time = datetime.datetime(year=2023, month=1, day=1)
        recording.add_activity(time, "test activity")
        key = list(recording.activity_tracker.keys())[0]
        self.assertEqual(key, time)

        recording = Recording.read("tests/data")
        key = list(recording.activity_tracker.keys())[0]
        self.assertEqual(key, time)

        time = datetime.datetime(year=2023, month=1, day=2)
        recording.add_activity(time, "test activity")
        self.assertEqual(len(recording.activity_tracker), 2)

        recording = Recording.read("tests/data")
        self.assertEqual(len(recording.activity_tracker), 2)
