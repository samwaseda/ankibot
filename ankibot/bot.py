# This example show how to use inline keyboards and process button presses
import logging
import numpy as np
import os
import pandas as pd
import telebot
from dataclasses import dataclass
from datetime import datetime, timedelta
from hashlib import sha1

from algorithm import load_data, get_options


with open("token", "r") as f:
    TELEGRAM_TOKEN = f.read().split("\n")[0]

DATA_DIR = "data"  # folder with your .apkg files
os.makedirs(DATA_DIR, exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

user_data = {}


@dataclass
class UserData:
    df: pd.DataFrame
    deck: str
    p: list


bot = telebot.TeleBot(TELEGRAM_TOKEN)


@bot.message_handler(commands=['start'])
def start(message):
    logger.info(
        f"User {message.from_user.id} with the user name {message.from_user.username} started the bot."
    )
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


def get_probability_file(user_id, df):
    return f"user/{user_id}_{sha1(df.to_json().encode()).hexdigest()}.dat"

def load_probability(user_id, df):
    file_path = get_probability_file(user_id, df)
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return np.array(list(map(int, f.read().split())))
    else:
        return np.ones(len(df)).astype(int)

def save_probability(user_id, df, p):
    file_path = get_probability_file(user_id, df)
    with open(file_path, "w") as f:
        f.write(" ".join(map(str, p)))

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    logger.info(f"Callback from user {call.from_user.username}: {call.data}")
    if call.data.startswith("import_"):
        deck_name = call.data.split("import_")[1]
        try:
            df = load_data(os.path.join(DATA_DIR, deck_name))
            p = load_probability(call.from_user.id, df)
            user_data[call.from_user.id] = UserData(df=df, deck=deck_name, p=p)
            count = len(p)
            bot.answer_callback_query(call.id, f"Imported {count} cards from {deck_name} ✅")
        except Exception as e:
            logger.error(f"Error importing deck: {e}")
            bot.answer_callback_query(call.id, "Failed to import deck. Please check logs.")
    elif call.data.startswith("answer::"):
        if user_data.get(call.from_user.id) is None:
            bot.answer_callback_query(call.id, "Please import a deck (again)")
            return
        parts = call.data.split("::")
        answer_type = parts[1]
        index = int(parts[-1])

        if answer_type == "correct":
            response_text = "Correct!"
            # Update probability logic here
            user_data[call.from_user.id].p[index] -= 1
        else:
            correct_answer = parts[2]
            response_text = f"Correct answer: {correct_answer}"
            # Update probability logic here
            user_data[call.from_user.id].p[index] += 1
        bot.send_message(
            call.message.chat.id,
            response_text
        )
        save_probability(call.from_user.id, user_data[call.from_user.id].df, user_data[call.from_user.id].p)
    logger.info(f"Processing review for user {call.from_user.id}")
    review(call.from_user.id)

def review(user_id):
    logger.info(f"Reviewing for user {user_id}")
    index, choice, options = get_options(
        user_data[user_id].df,
        p=user_data[user_id].p,
        n=4
    )
    correct_answer = choice["answer"]
    keyboard = []
    sub_keyboard = []
    for ii, key in enumerate(options + ["I don't know"]):
        if key == correct_answer:
            txt = f"answer::correct::{index}"
        else:
            txt = f"answer::incorrect::{correct_answer}::{index}"
        button = telebot.types.InlineKeyboardButton(
            text=key,
            callback_data=txt
        )
        sub_keyboard.append(button)
        if ii % 2 == 1 or ii == len(options):
            keyboard.append(sub_keyboard)
            sub_keyboard = []
    bot.send_message(
        user_id,
        choice["question"],
        reply_markup=telebot.types.InlineKeyboardMarkup(
            keyboard=keyboard
        )
    )


def main():
    bot.infinity_polling()

if __name__ == "__main__":
    main()
