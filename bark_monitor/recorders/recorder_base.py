from abc import abstractmethod
from datetime import datetime, timedelta
from typing import Callable, Optional

from bark_monitor.recorders.recording import Recording


class RecorderBase:
    def __init__(
        self,
        bark_func: Optional[Callable[[int], None]] = None,
        stop_bark_func: Optional[Callable[[timedelta], None]] = None,
    ) -> None:
        self._bark_level: int = 0
        self.bark_func = bark_func
        self.stop_bark_func = stop_bark_func

        self._barking_at = datetime.now()
        self._is_barking = False
        self.running = False
        self.is_paused = False

    @property
    def bark_level(self) -> Optional[int]:
        return self._bark_level

    def _init(self):
        self._barking_at = datetime.now()
        self._is_barking = False
        recording = Recording.read()
        recording.start = datetime.now()
        self.running = True

    def record(self):
        self._init()
        self._record()

    @abstractmethod
    def _record(self):
        raise NotImplementedError()

    def stop(self):
        self.running = False
        recording = Recording.read()
        recording.time_barked = self.total_time_barking
        recording.end(datetime.now())
        self._bark_level = 0
        self._stop()

    @abstractmethod
    def _stop(self):
        raise NotImplementedError()

    def _is_bark(self, value: int) -> bool:
        if self._bark_level == 0:
            return False
        return value >= self._bark_level

    @abstractmethod
    def _set_bark_level(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def _save_recording(self):
        raise NotImplementedError()

    def _intensity_decision(self, intensity: int) -> None:
        is_bark = self._is_bark(intensity)
        # If to update time and stop recording the bark
        if is_bark:
            self._barking_at = datetime.now()
            if not self._is_barking:
                self._is_barking = True
                if self.bark_func is not None:
                    self.bark_func(intensity - self._bark_level)
        elif self._is_barking and (datetime.now() - self._barking_at) > timedelta(
            seconds=1
        ):
            assert self._barking_at is not None
            self._is_barking = False
            self.total_time_barking = self.total_time_barking + (
                datetime.now() - self._barking_at
            )

            if self.stop_bark_func is not None:
                self.stop_bark_func(datetime.now() - self._barking_at)
            self._save_recording()
            self._frames = []
