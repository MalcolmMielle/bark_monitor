from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from bark_monitor.bark import Bark
from bark_monitor.plot.plot_bark import plot_bark
from bark_monitor.recorder import Recorder


class VeryBarkBot:
    def __init__(self, bark_level: int) -> None:
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

        self._bark_level = bark_level

        self.recorder: Optional[Recorder] = None
        self.application.run_polling()

        self.stop_recorder_sync()

    @staticmethod
    def _filename() -> str:
        now = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        return str(Path("recordings", now + ".wav"))

    async def start_recorder(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        assert update.effective_chat is not None
        self.recorder = Recorder(
            self._filename(), self._bark_level, self.send_bark, self.send_end_bark
        )
        self.recorder.record_thread()
        await self.application.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Recorder started",
        )

    async def stop_recorder(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        assert update.effective_chat is not None
        self.stop_recorder_sync()
        await self.application.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Recorder stopped",
        )

    def stop_recorder_sync(self) -> None:
        if self.recorder is not None:
            self.recorder.stop_thread()
            bark = Bark(self.recorder.filename, threshold=self._bark_level)
            print(bark)
            plot_bark(bark, to_file=True)

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
        assert update.effective_chat is not None
        if self.recorder is not None:
            self.recorder.is_paused = True
        await self.application.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Recorder paused",
        )

    async def unpause(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        assert update.effective_chat is not None
        if self.recorder is not None:
            self.recorder.is_paused = False
        await self.application.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Recorder unpaused",
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
