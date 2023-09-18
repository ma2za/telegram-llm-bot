import logging
import os
from datetime import date

import mmh3
import openai
from async_lru import alru_cache

from telegram_smart_bots.shared.chat import azure_openai_chat
from telegram_smart_bots.shared.mongo import mongodb_manager

logger = logging.getLogger(__name__)


async def check_voice_limit(user_id, duration: int):
    db = mongodb_manager.get_database(os.getenv("DB_NAME"))
    collection = db["journals"]
    result = await collection.find_one(
        {"telegram_id": user_id},
        {
            f"journal.{date.today()}.daily_seconds": 1,
            "daily_voice_limit": 1,
        },
    )
    if result is None:
        result = {}
    daily_seconds = (
        result.get("journal", {}).get(f"{date.today()}", {}).get("daily_seconds", 0)
    )
    daily_voice_limit = result.get("daily_voice_limit", 300)
    # TODO handle split audio
    if daily_voice_limit - daily_seconds - duration < 0:
        raise Exception


@alru_cache
async def transcribe(
    voice: bytes, user_id: int, duration: int, language: str | None = None
) -> str:
    db = mongodb_manager.get_database(os.getenv("DB_NAME"))
    collection = db["journals"]
    file_name = f".tmp/{mmh3.hash(voice)}.oga"
    with open(file_name, "wb") as new_file:
        new_file.write(voice)
    trans_kwargs = {} if language is None else {"language": language}
    result = await openai.Audio.atranscribe(
        "whisper-1",
        open(file_name, "rb"),
        api_key=os.getenv("OPENAI_API_KEY"),
        **trans_kwargs,
    )
    os.remove(file_name)
    await collection.update_one(
        {"telegram_id": user_id},
        {"$inc": {f"journal.{date.today()}.daily_seconds": duration}},
        upsert=True,
    )
    return result.get("text").strip()


async def transcribe_and_edit(
    msg_date,
    downloaded_file,
    user_id,
    duration,
):
    db = mongodb_manager.get_database(os.getenv("DB_NAME"))
    collection = db["journals"]
    # TODO set daily limit
    msg_date = int(msg_date.timestamp())

    try:
        # TODO handle date.fromtimestamp(msg_date) everywhere
        await check_voice_limit(user_id, duration)

        result = await collection.find_one(
            {"telegram_id": user_id},
            {"editor_temperature": 1, "language": 1},
        )

        if result is None:
            result = {}

        transcript = await transcribe(
            bytes(downloaded_file),
            user_id,
            duration,
            result.get("language"),
        )

        temperature = result.get("editor_temperature", 0.1)
        if 0 <= temperature <= 1:
            transcript = await azure_openai_chat(transcript, temperature)

        await collection.update_one(
            {"telegram_id": user_id},
            {
                "$set": {
                    f"journal.{date.fromtimestamp(msg_date)}.messages.{msg_date}": transcript
                }
            },
            upsert=True,
        )
        reply_msg = f"{msg_date}:={transcript}"
    except Exception as ex:
        logger.error(ex)
        reply_msg = "😿"
    return reply_msg
