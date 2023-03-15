import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes


class VeryBarkBot:
    def __init__(self) -> None:
        with open("api_key") as f:
            self._api_key = f.readlines()[0]
        self.chat_ids = set()

        self.application = ApplicationBuilder().token(self._api_key).build()

        register_handler = CommandHandler("register", self.register)
        self.application.add_handler(register_handler)

    def init(self):
        self.application.run_polling()

    async def register(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        assert update.effective_chat is not None
        self.chat_ids.add(update.effective_chat.id)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="I will now let you know when Watson is barking!",
        )

    def send_bark(self):
        for chat in self.chat_ids:
            url = (
                f"https://api.telegram.org/"
                f"bot{self._api_key}/"
                f"sendMessage?chat_id={chat}&text=bark"
            )
            requests.get(url).json()
