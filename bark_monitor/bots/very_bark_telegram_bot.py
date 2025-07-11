from datetime import timedelta
from pathlib import Path

import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bark_monitor.bots.very_bark_bot import VeryBarkBot
from bark_monitor.chats import Chats
from bark_monitor.google_sync import BaseSync
from bark_monitor.recorders.base_recorder import BaseRecorder
from bark_monitor.recorders.recording import Recording


class VeryBarkTelegramBot(VeryBarkBot):
    def __init__(
        self,
        api_key: str,
        config_folder: Path,
        sync: BaseSync,
        accept_new_users: bool = False,
    ) -> None:
        self._api_key = api_key

        self._application = (
            ApplicationBuilder()
            .token(self._api_key)
            .get_updates_http_version("1.1")
            .http_version("1.1")
            .pool_timeout(5)
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

        activity_handler = CommandHandler("activity", self.activity)
        self._application.add_handler(activity_handler)

        help_handler = CommandHandler("help", self.help)
        self._application.add_handler(help_handler)

        audio_handler = CommandHandler("audio", self.send_audio)
        self._application.add_handler(audio_handler)
        last_audio_handler = CommandHandler("last", self.last_audio)
        self._application.add_handler(last_audio_handler)

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("login", self.start_login_to_google_drive)],
            states={
                0: [
                    MessageHandler(
                        filters.TEXT,
                        self.create_credential_from_code,
                    ),
                ],
                1: [MessageHandler(filters.TEXT, self.already_logged_in_google_drive)],
            },
            fallbacks=[
                MessageHandler(
                    filters.Regex("^Done$"), self.start_login_to_google_drive
                )
            ],
        )

        self._application.add_handler(conv_handler)
        self._accept_new_users = accept_new_users
        self._sync = sync

    def start(self, recorder: BaseRecorder) -> None:
        super().start(recorder=recorder)

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
        chats.add(update.effective_chat.id)
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

        sync_status = self._sync.status()

        recording = Recording.read(
            output_folder=self._recorder.output_folder, sync_service=self._sync
        )
        status += "Time barked: " + str(recording.time_barked) + " -- " + sync_status
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

        recording = Recording.read(
            output_folder=self._recorder.output_folder, sync_service=self._sync
        )
        activities = recording.daily_activities_formated()

        if activities == "":
            await self._application.bot.send_message(
                chat_id=update.effective_chat.id,
                text="No activities today",
            )
            return

        activities = "Activities:\n" + activities

        await self._application.bot.send_message(
            chat_id=update.effective_chat.id,
            text=activities,
        )

    def send_bark(self, intensity: int) -> None:
        self.send_text("bark: " + str(intensity))

    def send_text(self, text: str) -> None:
        chats = Chats.read(self._config_folder)
        for chat in chats.chats:
            url = (
                f"https://api.telegram.org/"
                f"bot{self._api_key}/"
                f"sendMessage?chat_id={chat}&text=" + text
            )
            requests.get(url).json()

    def send_end_bark(self, time_barking: timedelta) -> None:
        self.send_text("barking stopped after: " + str(time_barking))

    async def send_audio(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        assert update.effective_chat is not None
        if not await self._is_registered(update.effective_chat.id, context):
            return

        async def error_message_audio_file(update: Update) -> None:
            assert update.message is not None
            await update.message.reply_text("Recordings of today:")
            for file in audio_folder.iterdir():
                await update.message.reply_text("/audio " + file.name)

        assert update.message is not None
        assert update.message.text is not None
        audio_folder = self._recorder.today_audio_folder

        if not audio_folder.exists() or len(list(audio_folder.iterdir())) == 0:
            await update.message.reply_text(
                "No recording today. Your dog has been a good boy :3"
            )
            return

        split_command = update.message.text.split(" ", 1)
        if len(split_command) == 1:
            await update.message.reply_text("no file specified.")
            await error_message_audio_file(update)
            return

        audio_file = Path(audio_folder, split_command[1])
        if not audio_file.exists():
            await update.message.reply_text(
                "Audio file " + str(audio_file) + " does not exists."
            )
            await error_message_audio_file(update)
            return

        with open(audio_file, mode="rb") as audio:
            await update.message.reply_audio(audio=audio)

    async def last_audio(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        assert update.message is not None
        assert update.effective_chat is not None
        if not await self._is_registered(update.effective_chat.id, context):
            return

        audio_folder = self._recorder.today_audio_folder
        audio_files = audio_folder.glob("*")
        audio_file = max(audio_files, key=lambda p: p.stat().st_ctime)

        with open(audio_file, mode="rb") as audio:
            await update.message.reply_audio(audio=audio)

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        assert update.effective_chat is not None
        if not await self._is_registered(update.effective_chat.id, context):
            return

        help_message = VeryBarkBot.Commands.help_message()
        await self._application.bot.send_message(
            chat_id=update.effective_chat.id,
            text=help_message,
        )

    async def start_login_to_google_drive(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Start the conversation to save file on Google Drive"""

        assert update.message is not None

        already_logged_in, authorize_url = self._sync.login()
        if already_logged_in:
            return 1

        assert update.message is not None
        await update.message.reply_text(
            "Go to the following link in your browser: "
            + authorize_url
            + " and enter the code",
        )
        return 0

    async def already_logged_in_google_drive(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        assert update.message is not None
        await update.message.reply_text(
            "Already logged in",
        )
        return ConversationHandler.END

    async def create_credential_from_code(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Create credential for google drive from received code in previous step"""
        assert update.message is not None

        text = update.message.text
        assert text is not None

        await update.message.reply_text(
            "Neat! the code is: " + text,
        )

        self._sync.login_step_2(text=text)

        assert update.effective_chat is not None
        await self._application.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Login to Google",
        )

        return ConversationHandler.END
