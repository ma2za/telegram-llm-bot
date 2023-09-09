import json
import os

import requests
import yaml
from telegram import Update
from telegram.ext import ContextTypes

from telegram_llm_guru.db import mongodb_manager


async def chat(payload):
    headers = {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate",
        "Authorization": f"Basic {os.getenv('BEAM_TOKEN')}",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
    }

    response = requests.request(
        "POST",
        os.getenv("BEAM_URL"),
        headers=headers,
        data=json.dumps(payload),
        timeout=10000,
    )

    # TODO check httpx error 400 '{"Offset":1}'
    # async with httpx.AsyncClient() as client:
    #     response = await client.request(
    #         "POST",
    #         os.getenv("BEAM_URL"),
    #         headers=headers,
    #         data=payload,
    #         timeout=10000,
    #     )
    if response.status_code != 200:
        raise Exception
    out = response.json().get("message")
    return out.get("text").strip() if isinstance(out, dict) else out


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        db = mongodb_manager.get_database("travel-gurus")
        collection = db["guru"]

        result = collection.find_one({"telegram_id": update.message.from_user.id})
        if result is None:
            messages = []
            with open("scripts/config.yml", "r") as stream:
                config = yaml.load(stream, Loader=yaml.Loader)
            new_messages = [config.get("system"), update.message.text]

        else:
            messages = result.get("messages", [])
            new_messages = [update.message.text]
        payload = {"messages": messages + new_messages}
        response = await chat(payload)
        new_messages += [response]
        collection.update_one(
            {"telegram_id": update.message.from_user.id},
            {"$push": {"messages": {"$each": new_messages}}},
            upsert=True,
        )

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=response,
            reply_to_message_id=update.message.id,
        )
    except Exception as ex:
        print()
    finally:
        context.user_data[update.update_id] = "Done"
