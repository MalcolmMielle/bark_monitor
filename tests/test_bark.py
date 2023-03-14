import unittest

from dog_bark.bark import Bark


class TestBark(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._bark = Bark("tests/data/13mars.wav", step=100, threshold=4000)

    def test_extract(self):
        self.assertEqual(len(self._bark.amplitude_envelope), 573976)

    def test_time_barking(self):
        self.assertEqual(self._bark.time_spent_barking, 0.75)
