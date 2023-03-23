from datetime import timedelta

import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from bark_monitor.recorders.recorder_base import RecorderBase


class VeryBarkBot:
    def __init__(self, recorder: RecorderBase) -> None:
        with open("api_key") as f:
            self._api_key = f.readlines()[0]
        self.chat_ids = set()

        self.application = ApplicationBuilder().token(self._api_key).build()

        register_handler = CommandHandler("register", self.register)
        self.application.add_handler(register_handler)
        pause_handler = CommandHandler("pause", self.pause)
        self.application.add_handler(pause_handler)
        unpause_handler = CommandHandler("unpause", self.unpause)
        self.application.add_handler(unpause_handler)

        start_handler = CommandHandler("start", self.start_recorder)
        self.application.add_handler(start_handler)
        stop_handler = CommandHandler("stop", self.stop_recorder)
        self.application.add_handler(stop_handler)

        status_handler = CommandHandler("status", self.status)
        self.application.add_handler(status_handler)

        self.recorder = recorder
        self.recorder.bark_func = self.send_bark
        self.recorder.stop_bark_func = self.send_end_bark

        self.application.run_polling()

        self._stop_recorder_sync()

    async def _is_recording(self, update: Update) -> bool:
        if not self.recorder.running:
            assert update.effective_chat is not None
            await self.application.bot.send_message(
                chat_id=update.effective_chat.id,
                text="The program is not recording",
            )
        return self.recorder.running

    async def start_recorder(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        assert update.effective_chat is not None
        if self.recorder.running:
            await self.application.bot.send_message(
                chat_id=update.effective_chat.id,
                text="The program is already recording",
            )
            return

        self.recorder.record()
        await self.application.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Recorder started",
        )

    async def stop_recorder(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if not await self._is_recording(update):
            return

        assert update.effective_chat is not None
        self._stop_recorder_sync()
        await self.application.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Recorder stopped",
        )

    def _stop_recorder_sync(self) -> None:
        if self.recorder.running is True:
            self.recorder.stop()
            print("The dog barked for:", self.recorder.total_time_barking)

    async def register(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        assert update.effective_chat is not None
        self.chat_ids.add(update.effective_chat.id)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="I will now let you know when Watson is barking!",
        )

    async def pause(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self._is_recording(update):
            return

        assert update.effective_chat is not None
        self.recorder.is_paused = True
        await self.application.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Recorder paused",
        )

    async def unpause(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self._is_recording(update):
            return

        assert update.effective_chat is not None
        self.recorder.is_paused = False
        await self.application.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Recorder unpaused",
        )

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self._is_recording(update):
            return

        assert update.effective_chat is not None
        status = "The program is recording"
        if self.recorder.is_paused:
            status = "The program is paused"
        await self.application.bot.send_message(
            chat_id=update.effective_chat.id,
            text=status,
        )

    def send_bark(self, intensity: int) -> None:
        for chat in self.chat_ids:
            url = (
                f"https://api.telegram.org/"
                f"bot{self._api_key}/"
                f"sendMessage?chat_id={chat}&text=bark: " + str(intensity)
            )
            requests.get(url).json()

    def send_end_bark(self, time_barking: timedelta) -> None:
        for chat in self.chat_ids:
            url = (
                f"https://api.telegram.org/"
                f"bot{self._api_key}/"
                f"sendMessage?chat_id={chat}&text=barking stopped after: "
                + str(time_barking)
            )
            requests.get(url).json()
