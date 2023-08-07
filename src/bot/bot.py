import json
import os

import requests
import telebot
import yaml
from dotenv import load_dotenv

load_dotenv()

with open("config.yml", 'r') as stream:
    config = yaml.load(stream, Loader=yaml.Loader)

SYSTEM = config.get("system")

messages = []
bot = telebot.TeleBot(os.getenv("TELEGRAM_BOT_TOKEN"), parse_mode=None)


def chat(payload):
    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate",
        "Authorization": f"Basic {os.getenv('BEAM_TOKEN')}",
        "Connection": "keep-alive",
        "Content-Type": "application/json"
    }

    response = requests.request("POST", os.getenv("BEAM_URL"),
                                headers=headers,
                                data=json.dumps(payload),
                                timeout=1000
                                )
    out = response.json().get('message')
    return out.get("text") if isinstance(out, dict) else out


@bot.message_handler(commands=['record'])
def record(message):
    """
    This is an example of how to implement a specific function for a special
    command. You can replace them main system prompt, with a specific prompt.
    :param message:
    """
    if os.getenv('BEAM_TOKEN') is None or os.getenv("BEAM_URL") is None:
        bot.reply_to(message, "Beam environment variables not set!")
        return
    payload = {
        "system": config.get("record"),
        "messages": messages
    }
    bot.reply_to(message, chat(payload))


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if os.getenv('BEAM_TOKEN') is None or os.getenv("BEAM_URL") is None:
        bot.reply_to(message, "Beam environment variables not set!")
        return
    payload = {
        "system": SYSTEM,
        "messages": [config.get("start")]
    }
    bot.reply_to(message, chat(payload))


@bot.message_handler(func=lambda msg: True)
def conversation(message):
    if os.getenv('BEAM_TOKEN') is None or os.getenv("BEAM_URL") is None:
        bot.reply_to(message, "Beam environment variables not set!")
        return
    messages.append(message.text)
    payload = {
        "system": SYSTEM,
        "messages": messages
    }
    response = chat(payload)
    messages.append(response)
    bot.reply_to(message, response)


bot.infinity_polling()
