import os
from telegram import Bot

bot = Bot(token=os.environ['TELEGRAM_BOT_TOKEN'])
ADMIN_CHAT_ID = int(os.environ['TELEGRAM_ADMIN_CHAT_ID'])

def send_message(text: str) -> None:
    bot.send_message(chat_id=ADMIN_CHAT_ID, text=text)
