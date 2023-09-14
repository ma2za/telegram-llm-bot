import os

import httpx
import yaml
from telegram import Update
from telegram.ext import ContextTypes

from telegram_llm_guru.db import mongodb_manager


async def chat(payload):
    async with httpx.AsyncClient() as client:
        response = await client.request(
            "POST",
            os.getenv("BEAM_URL"),
            headers={
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate",
                "Authorization": f"Basic {os.getenv('BEAM_TOKEN')}",
                "Connection": "keep-alive",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=10000,
        )
    response.raise_for_status()
    out = response.json().get("message")
    return out.get("text").strip() if isinstance(out, dict) else out


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = mongodb_manager.get_database("travel-gurus")
    collection = db["guru"]
    msg_reply = "😿"
    try:
        result = await collection.find_one({"telegram_id": update.message.from_user.id})
        if result is None:
            messages = []
            with open("scripts/config.yml", "r") as stream:
                config = yaml.load(stream, Loader=yaml.Loader)
            new_messages = [config.get("system"), update.message.text]
        else:
            messages = result.get("messages", [])
            new_messages = [update.message.text]
        response = await chat({"messages": messages + new_messages})
        new_messages += [response]
        await collection.update_one(
            {"telegram_id": update.message.from_user.id},
            {"$push": {"messages": {"$each": new_messages}}},
            upsert=True,
        )
        msg_reply = response
    except Exception as ex:
        msg_reply = "😿"
    finally:
        context.user_data[update.update_id] = "Done"
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=msg_reply,
            reply_to_message_id=update.message.id,
        )
