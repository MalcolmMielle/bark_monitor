from datetime import datetime, timedelta
from typing import Optional

import numpy as np

from bark_monitor.recorders.base_recorder import BaseRecorder
from bark_monitor.recorders.recording import Recording


class Recorder(BaseRecorder):
    """A recorder using signal amplitude to detect dog barks."""

    def __init__(
        self,
        api_key: str,
        config_folder: str,
        output_folder: str,
        accept_new_users: bool = False,
    ) -> None:
        self._bark_level: int = 0

        self.running = False
        self.is_paused = False

        self._last_bark = datetime.now()
        super().__init__(
            api_key, config_folder, output_folder, accept_new_users=accept_new_users
        )

    @property
    def bark_level(self) -> Optional[int]:
        return self._bark_level

    def _init(self):
        super()._init()
        self._barking_at = datetime.now()
        self._is_barking = False

    def _is_bark(self, value: int) -> bool:
        if self._bark_level == 0:
            return False
        return value >= self._bark_level

    def _signal_to_intensity(self, signal: bytes) -> int:
        np_data = np.frombuffer(signal, dtype=np.int16)
        return np.amax(np_data)  # type: ignore

    def stop(self):
        self._bark_level = 0
        return super().stop()

    def _set_bark_level(self, range_measurements: int = 100) -> None:
        assert self._stream is not None
        self._bark_level = 0
        for _ in range(range_measurements):
            data = self._stream.read(self._chunk)
            self._bark_level = max(self._bark_level, self._signal_to_intensity(data))
        self._bark_level *= 2

    def _record_loop(self) -> None:
        self._start_stream()
        self._bark_logger.info("Recording started")

        assert self._stream is not None
        self._set_bark_level()

        while self.running:
            if self.is_paused:
                continue

            data = self._stream.read(self._chunk, exception_on_overflow=False)
            intensity = self._signal_to_intensity(data)

            # Save data if dog is barking
            is_bark = self._is_bark(intensity)
            if is_bark:
                self._frames.append(data)

            # If to update time and stop recording the bark
            if is_bark:
                self._barking_at = datetime.now()
                if not self._is_barking:
                    self._is_barking = True
                    self._chat_bot.send_bark(intensity - self._bark_level)

            elif self._is_barking and (datetime.now() - self._barking_at) > timedelta(
                seconds=5
            ):
                assert self._barking_at is not None
                self._is_barking = False

                recording = Recording.read(self.output_folder)
                duration = timedelta(
                    seconds=(len(self._frames) * self._chunk) / self._fs
                )
                recording.add_time_barked(duration)

                self._chat_bot.send_end_bark(duration)
                self._save_recording(self._frames)
                self._frames = []

        self._stop_stream()
