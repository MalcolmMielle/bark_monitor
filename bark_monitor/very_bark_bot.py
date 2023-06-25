import shutil
from datetime import timedelta
from enum import Enum
from pathlib import Path
from typing import Optional

import oauth2client.client
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bark_monitor.chats import Chats
from bark_monitor.recorders.recording import Recording


class Commands(Enum):
    help = "Display a help message"
    activity = "Display the day activity of the pets"
    start = "Start the recorder"
    stop = "Stop the recorder"
    pause = "Pause the recorder"
    unpause = "Unpause the recorder"
    bark_level = (
        "If using amplitude base recording, show the threshold to detect a bark"
    )
    register = "Register a new user"
    status = "Status of the recorder"
    save = "Save to google drive"
    login = "Log in to google drive"

    @staticmethod
    def help_message() -> str:
        msg = ""
        for e in Commands:
            msg += e.name + " - " + e.value + "\n"
        return msg


class VeryBarkBot:
    def __init__(
        self,
        api_key: str,
        config_folder: str,
        recorder: "BaseRecorder",  # noqa F821
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
        bark_level_handler = CommandHandler("bark_level", self.bark_level)
        self._application.add_handler(bark_level_handler)

        activity_handler = CommandHandler("activity", self.activity)
        self._application.add_handler(activity_handler)

        help_handler = CommandHandler("help", self.help)
        self._application.add_handler(help_handler)

        save_handler = CommandHandler("save", self.save)
        self._application.add_handler(save_handler)

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("login", self.start_login_to_google_drive)],
            states={
                0: [
                    MessageHandler(
                        filters.TEXT,
                        self.create_credential_from_code,
                    ),
                ],
                1: [MessageHandler(filters.TEXT, self.already_loged_in_google_drive)],
            },
            fallbacks=[
                MessageHandler(
                    filters.Regex("^Done$"), self.start_login_to_google_drive
                )
            ],
        )

        self._application.add_handler(conv_handler)

        self._accept_new_users = accept_new_users

        self._recorder = recorder
        self._scopes = ["https://www.googleapis.com/auth/drive.file"]
        self._code_google_drive: Optional[str] = None
        self.flow = None

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
        if len(recording.activity_tracker) == 0:
            await self._application.bot.send_message(
                chat_id=update.effective_chat.id,
                text="No activities today",
            )
            return

        activities = "Activities:\n"
        for datetime, activity in recording.activity_tracker.items():
            activities += datetime.strftime("%H %M %S") + ": " + activity + "\n"
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

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        assert update.effective_chat is not None
        if not await self._is_registered(update.effective_chat.id, context):
            return

        help_message = Commands.help_message()
        await self._application.bot.send_message(
            chat_id=update.effective_chat.id,
            text=help_message,
        )

    async def start_login_to_google_drive(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        """Start the conversation to save file on Google Drive"""

        got_cred, _ = self._get_cred()
        if got_cred:
            return 1

        self.flow = oauth2client.client.flow_from_clientsecrets(
            "credentials.json", self._scopes
        )
        self.flow.redirect_uri = oauth2client.client.OOB_CALLBACK_URN
        authorize_url = self.flow.step1_get_authorize_url()
        assert update.message is not None
        await update.message.reply_text(
            "Go to the following link in your browser: "
            + authorize_url
            + " and enter the code",
        )
        return 0

    async def already_loged_in_google_drive(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> int:
        assert update.message is not None
        await update.message.reply_text(
            "Already loged in",
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

        assert self.flow is not None
        creds = self.flow.step2_exchange(text)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

        assert update.effective_chat is not None
        await self._application.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Login to Google",
        )

        return ConversationHandler.END

    def _get_cred(self) -> tuple[bool, Optional[Credentials]]:
        """Check if connected to google drive already"""
        creds = None
        if Path("token.json").exists():
            creds = Credentials.from_authorized_user_file("token.json", self._scopes)
        # If there are no (valid) credentials available, let the user log in.
        if creds and creds.valid:
            return True, Credentials.from_authorized_user_file(
                "token.json", self._scopes
            )
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            return True, Credentials.from_authorized_user_file(
                "token.json", self._scopes
            )
        return False, None

    async def save(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Save recording folder as a zip file in google drive"""
        assert update.effective_chat is not None
        got_cred, creds = self._get_cred()
        if not got_cred:
            await self._application.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Please login to google first",
            )

        try:
            # create drive api client
            service = build("drive", "v3", credentials=creds)

            shutil.make_archive("recordings", "zip", self._recorder.output_folder)
            file_metadata = {"name": "recordings.zip"}
            media = MediaFileUpload("recordings.zip")
            file = (
                service.files()
                .create(body=file_metadata, media_body=media, fields="id")
                .execute()
            )
            await self._application.bot.send_message(
                chat_id=update.effective_chat.id, text="Saved file " + file.get("id")
            )

        except HttpError as error:
            await self._application.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Error upload to google: " + str(error),
            )
