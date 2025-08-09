# This example show how to use inline keyboards and process button presses
import logging
import os
import pandas as pd
import telebot
from dataclasses import dataclass
from datetime import datetime, timedelta

from algorithm import load_data


with open("token", "r") as f:
    TELEGRAM_TOKEN = f.read().split("\n")[0]

DATA_DIR = "data"  # folder with your .apkg files
os.makedirs(DATA_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

user_dataframe = {}


@dataclass
class UserData:
    df: pd.DataFrame = None
    deck: str = None


bot = telebot.TeleBot(TELEGRAM_TOKEN)


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        "Welcome to the Anki Flashcard Bot!\n"
        "Commands:\n"
        "/listdecks - Show available decks\n"
        "/review - Start reviewing due cards"
    )

@bot.message_handler(commands=['listdecks'])
def list_decks(message):
    decks = [f for f in os.listdir(DATA_DIR) if f.endswith(".yml") and not f.startswith("SBF")]
    if not decks:
        bot.send_message(message.chat.id, "No decks available.")
        return
    keyboard = telebot.types.InlineKeyboardMarkup()
    for deck in decks:
        button = telebot.types.InlineKeyboardButton(
            text=deck, callback_data=f"import_{deck}"
        )
        keyboard.add(button)
    bot.send_message(message.chat.id, "Available decks:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    if call.data.startswith("import_"):
        deck_name = call.data.split("import_")[1]
        try:
            user_dataframe[call.from_user.id] = UserData(
                df=load_data(os.path.join(DATA_DIR, deck_name)), deck=deck_name
            )
            count = len(user_dataframe[call.from_user.id].df)
            bot.answer_callback_query(call.id, f"Imported {count} cards from {deck_name} ✅")
        except Exception as e:
            logger.error(f"Error importing deck: {e}")
            bot.answer_callback_query(call.id, "Failed to import deck. Please check logs.")

@bot.message_handler(commands=['review'])
def review(message):
    card = get_due_card(message.from_user.id)
    if not card:
        bot.send_message(message.chat.id, "No due cards available.")
        return
    card_id, front, back, interval, ease, repetitions = card
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keys = ["Turn around", "Again", "Good", "Easy"]
    for key in keys:
        button = telebot.types.KeyboardButton(
            text=key, callback_data=f"answer_{card_id}:{interval}:{ease}:{repetitions}:{key}"
        )
        keyboard.add(button)
    bot.send_message(
        message.chat.id,
        front,
        reply_markup=keyboard,
    )


def main():
    bot.infinity_polling()

if __name__ == "__main__":
    main()
