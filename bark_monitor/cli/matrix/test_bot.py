from pathlib import Path

import niobot
import tyro

from bark_monitor.base_sync import BaseSync
from bark_monitor.bots.very_bark_matrix_bot import VeryBarkMatrixBot
from bark_monitor.fake_sync import FakeSync
from bark_monitor.recorders.fake_recorder import FakeRecorder


class FakeVeryBarkMatrixBot(VeryBarkMatrixBot):
    _recorder: FakeRecorder

    def __init__(
        self,
        homeserver: str,
        user_id: str,
        password: str,
        config_folder: Path,
        sync: BaseSync,
    ) -> None:
        super().__init__(homeserver, user_id, password, config_folder, sync)

        fake_bark_command = niobot.Command(name="fake", callback=self.fake)
        self._bot.add_command(fake_bark_command)

    async def fake(self, ctx: niobot.Context) -> None:
        self._recorder.add_bark()


def main(homeserver: str, user_id: str, password: str):
    sync_service = FakeSync()
    matrix_bot = FakeVeryBarkMatrixBot(
        config_folder=Path("config"),
        sync=sync_service,
        homeserver=homeserver,
        user_id=user_id,
        password=password,
    )
    recorder = FakeRecorder(
        sync=sync_service,
        output_folder=Path(""),
        framerate=0,
        send_text_callback=matrix_bot.send_text,
    )
    matrix_bot.start(recorder=recorder)


if __name__ == "__main__":
    tyro.cli(main)
