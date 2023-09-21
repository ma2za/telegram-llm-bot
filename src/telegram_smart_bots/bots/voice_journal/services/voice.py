import logging
import os
from datetime import datetime

from langchain.schema import HumanMessage, SystemMessage
from openai import InvalidRequestError

from telegram_smart_bots.bots.voice_journal.services.text import add_text
from telegram_smart_bots.shared.audio import transcribe_and_check
from telegram_smart_bots.shared.chat import azure_openai_chat
from telegram_smart_bots.shared.db.mongo import mongodb_manager

logger = logging.getLogger(__name__)


async def voice_chat(
    audio: bytes, user_id: int, duration: int, msg_date: datetime
) -> str:
    try:
        transcript = await transcribe_and_check(audio, user_id, duration)
        reply_msg = await edit_text(transcript, user_id, msg_date)
    except InvalidRequestError as ex:
        logger.error(ex)
        reply_msg = str(ex)
    except Exception as ex:
        logger.error(ex)
        reply_msg = "😿"
    return reply_msg


async def set_openai_editor(user_id: int, temperature: float = None, text: str = None):
    db = mongodb_manager.get_database(os.getenv("BOT_NAME"))
    collection = db[os.getenv("COLLECTION_NAME")]
    try:
        if text is None:
            temp = float(temperature) if temperature is not None else 0.0
            await collection.update_one(
                {"user_id": user_id},
                {"$set": {"editor": temp}},
                upsert=True,
            )

            reply_msg = f"New temperature for editor {user_id}: {temp}"
        else:
            temp = float(temperature) if temperature is not None else None
            msg_date, old_text = text.split(":=")
            reply_msg = await edit_text(
                old_text.strip(),
                user_id,
                datetime.fromtimestamp(float(msg_date.strip())),
                temp,
            )
    except Exception as ex:
        logger.error(ex)
        reply_msg = "😿"
    return reply_msg


async def edit_text(
    text: str, user_id: int, msg_date: datetime, temperature: float = None
):
    db = mongodb_manager.get_database(os.getenv("BOT_NAME"))
    collection = db[os.getenv("COLLECTION_NAME")]
    if temperature is None:
        result = await collection.find_one({"user_id": user_id}, {"editor": 1})
        temperature = 0.0 if result is None else result.get("editor", 0.0)
    if 0 <= temperature <= 1:
        messages = [
            SystemMessage(
                content="""Edit, enhance, and refine the following text to resemble a travel journal infused
                with a gonzo, vivid, truthful and outrageous style. Maintain the original content, style, and language while
                improving readability. Embrace the chaotic and adventurous tone, and do not invent events or details
                not present in the original text. Preserve any curse words and the speaker's unique voice."""
            ),
            HumanMessage(content=text),
        ]

        text = await azure_openai_chat(messages, temperature)

    reply_msg = await add_text(user_id, msg_date, text)
    return reply_msg
