import asyncio
from pathlib import Path

import niobot

from bark_monitor.base_sync import BaseSync
from bark_monitor.bots.very_bark_bot import VeryBarkBot
from bark_monitor.chats import Chats
from bark_monitor.recorders.base_recorder import BaseRecorder
from bark_monitor.recorders.recording import Recording


class VeryBarkMatrixBot(VeryBarkBot):
    _recorder: BaseRecorder

    def __init__(
        self,
        homeserver: str,
        user_id: str,
        password: str,
        config_folder: Path,
        sync: BaseSync,
    ) -> None:
        self._bot = niobot.NioBot(
            homeserver=homeserver,
            user_id=user_id,
            command_prefix="!",
            ignore_self=True,
            store_path="./store",
        )
        self._password = password
        self._config_folder = config_folder
        self._sync = sync

        command = niobot.Command(name="ping", callback=self.ping)
        self._bot.add_command(command)

        start_command = niobot.Command(
            name="start_recorder", callback=self.start_recorder
        )
        self._bot.add_command(start_command)

        register_command = niobot.Command(name="register", callback=self.register)
        self._bot.add_command(register_command)

        stop_command = niobot.Command(name="stop_recorder", callback=self.stop_recorder)
        self._bot.add_command(stop_command)

        status_command = niobot.Command(name="status", callback=self.status)
        self._bot.add_command(status_command)

    def start(self, recorder: BaseRecorder) -> None:
        self._recorder = recorder
        self._bot.run(password=self._password)

    async def ping(self, ctx: niobot.Context) -> None:
        latency_ms = self._bot.latency(ctx.message)
        await ctx.respond("Pong! Latency: {:.2f}ms".format(latency_ms))

    async def start_recorder(self, ctx: niobot.Context):
        if self._recorder.running:
            await ctx.respond("The program is already running")
            return
        self._recorder.record()
        await ctx.respond("The program is running")

    async def stop_recorder(self, ctx: niobot.Context):
        if not self._recorder.running:
            await ctx.respond("The program was not running")
            return
        self._stop_recorder_sync()
        await ctx.respond("The program is stopped")

    def send_text(self, text: str) -> None:
        print("Send text")
        chats = Chats.read(self._config_folder)
        for chat in chats.chats:
            assert isinstance(chat, str)
            assert self._bot.loop is not None
            task = asyncio.create_task(self._bot.send_message(chat, text))
            task.add_done_callback(lambda _: None)
            task.result()

    async def register(self, ctx: niobot.Context) -> None:
        chats = Chats.read(self._config_folder)
        chats.add(ctx.message.sender)
        await ctx.respond("Registered " + ctx.message.sender)

    async def status(self, ctx: niobot.Context) -> None:
        status = "The program is not recording. "
        if not self._recorder.running:
            status = "The program is not recording. "
        if self._recorder.is_paused:
            status = "The program is paused. "
        recording = Recording.read(
            output_folder=self._recorder.output_folder, sync_service=self._sync
        )
        sync_status = self._sync.status()
        status += "Time barked: " + str(recording.time_barked) + " -- " + sync_status
        await ctx.respond(status)
