from datetime import timedelta

import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from bark_monitor.chats import Chats
from bark_monitor.recorders.recording import Recording


class VeryBarkBot:
    def __init__(
        self,
        api_key: str,
        config_folder: str,
        recorder: "BaseRecorder",
        accept_new_users: bool = False,
    ) -> None:
        self._api_key = api_key

        self._application = (
            ApplicationBuilder()
            .token(self._api_key)
            .get_updates_http_version("1.1")
            .http_version("1.1")
            .build()
        )

        self._config_folder = config_folder

        register_handler = CommandHandler("register", self.register)
        self._application.add_handler(register_handler)
        pause_handler = CommandHandler("pause", self.pause)
        self._application.add_handler(pause_handler)
        unpause_handler = CommandHandler("unpause", self.unpause)
        self._application.add_handler(unpause_handler)

        start_handler = CommandHandler("start", self.start_recorder)
        self._application.add_handler(start_handler)
        stop_handler = CommandHandler("stop", self.stop_recorder)
        self._application.add_handler(stop_handler)

        status_handler = CommandHandler("status", self.status)
        self._application.add_handler(status_handler)
        bark_level_handler = CommandHandler("bark_level", self.bark_level)
        self._application.add_handler(bark_level_handler)

        activity_handler = CommandHandler("activity", self.activity)
        self._application.add_handler(activity_handler)

        self._accept_new_users = accept_new_users

        self._recorder = recorder

    def start(self) -> None:
        chats = Chats.read(self._config_folder)
        for chat in chats.chats:
            url = (
                f"https://api.telegram.org/"
                f"bot{self._api_key}/"
                f"sendMessage?chat_id={chat}&text=Bot is ready with "
                + self._recorder.__class__.__name__
            )
            requests.get(url).json()
        self._application.run_polling()
        self._stop_recorder_sync()

    async def _is_recording(self, update: Update, signal_to_user: bool = True) -> bool:
        if not self._recorder.running:
            assert update.effective_chat is not None
            if signal_to_user:
                await self._application.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="The program is not recording",
                )
        return self._recorder.running

    async def start_recorder(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        assert update.effective_chat is not None
        if not await self._is_registered(update.effective_chat.id, context):
            return

        chats = Chats.read(self._config_folder)
        if self._recorder.running:
            await self._application.bot.send_message(
                chat_id=update.effective_chat.id,
                text="The program is already recording",
            )
            return

        self._recorder.record()
        for chat in chats.chats:
            await self._application.bot.send_message(
                chat_id=chat,
                text="Recorder started",
            )

    async def stop_recorder(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        assert update.effective_chat is not None
        if not await self._is_registered(update.effective_chat.id, context):
            return

        chats = Chats.read(self._config_folder)
        if not await self._is_recording(update):
            return
        self._stop_recorder_sync()
        for chat in chats.chats:
            await self._application.bot.send_message(
                chat_id=chat,
                text="Recorder stopped",
            )

    def _stop_recorder_sync(self) -> None:
        if self._recorder.running is True:
            self._recorder.stop()

    async def register(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        assert update.effective_chat is not None
        if not self._accept_new_users:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="New users cannot be registered",
            )
            return
        chats = Chats.read(self._config_folder)
        chats.add(update.effective_chat)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="I will now let you know when Watson is barking!",
        )

    async def _is_registered(self, id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
        chats = Chats.read(self._config_folder)
        is_registered = id in chats.chats
        if not is_registered:
            await context.bot.send_message(
                chat_id=id,
                text="You are not registered to this bot",
            )
        return is_registered

    async def pause(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        assert update.effective_chat is not None

        if not await self._is_recording(update) or not await self._is_registered(
            update.effective_chat.id, context
        ):
            return

        self._recorder.is_paused = True
        await self._application.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Recorder paused",
        )

    async def unpause(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        assert update.effective_chat is not None
        if not await self._is_recording(update) or not await self._is_registered(
            update.effective_chat.id, context
        ):
            return

        self._recorder.is_paused = False
        await self._application.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Recorder unpaused",
        )

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        assert update.effective_chat is not None
        if not await self._is_registered(update.effective_chat.id, context):
            return

        status = "The program is not recording. "

        if await self._is_recording(update, signal_to_user=False):
            status = "The program is recording. "
            if self._recorder.is_paused:
                status = "The program is paused. "

        recording = Recording.read(self._recorder.output_folder)
        status += "Time barked: " + str(recording.time_barked)
        await self._application.bot.send_message(
            chat_id=update.effective_chat.id,
            text=status,
        )

    async def activity(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        assert update.effective_chat is not None
        if not await self._is_registered(update.effective_chat.id, context):
            return

        recording = Recording.read(self._recorder.output_folder)
        activities = ""
        for datetime, activity in recording.activity_tracker.items():
            activities += activity + " at " + str(datetime) + "\n"
        await self._application.bot.send_message(
            chat_id=update.effective_chat.id,
            text=activities,
        )

    async def bark_level(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        assert update.effective_chat is not None
        if not await self._is_registered(update.effective_chat.id, context):
            return

        try:
            await self._application.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Level " + str(self._recorder.bark_level),
            )
        except Exception as e:
            await self._application.bot.send_message(
                chat_id=update.effective_chat.id,
                text="No bark level: " + str(e),
            )

    def send_bark(self, intensity: int) -> None:
        chats = Chats.read(self._config_folder)
        for chat in chats.chats:
            url = (
                f"https://api.telegram.org/"
                f"bot{self._api_key}/"
                f"sendMessage?chat_id={chat}&text=bark: " + str(intensity)
            )
            requests.get(url).json()

    def send_end_bark(self, time_barking: timedelta) -> None:
        chats = Chats.read(self._config_folder)
        for chat in chats.chats:
            url = (
                f"https://api.telegram.org/"
                f"bot{self._api_key}/"
                f"sendMessage?chat_id={chat}&text=barking stopped after: "
                + str(time_barking)
            )
            requests.get(url).json()

    def send_event(self, event_type: str) -> None:
        chats = Chats.read(self._config_folder)
        for chat in chats.chats:
            url = (
                f"https://api.telegram.org/"
                f"bot{self._api_key}/"
                f"sendMessage?chat_id={chat}&text=detected: " + event_type
            )
            requests.get(url).json()
