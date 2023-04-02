import unittest
from datetime import timedelta
from unittest import mock

from bark_monitor.recorders.recording import Recording


class TestRecording(unittest.TestCase):
    @mock.patch.object(Recording, "folder", return_value="tests/data/")
    def test_goal(self, _: Recording):
        recording = Recording.read()
        self.assertEqual(recording.time_barked, timedelta(1))
        self.assertEqual(len(recording.start_end), 1)
        self.assertEqual(recording.start_end[0], ["19:39:32.163523", "20:04:41.614984"])
