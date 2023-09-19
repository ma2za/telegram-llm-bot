import logging
import os
from datetime import date

import mmh3
import openai
from async_lru import alru_cache
from langchain.schema import SystemMessage, HumanMessage

from telegram_smart_bots.shared.chat import azure_openai_chat
from telegram_smart_bots.shared.db.mongo import mongodb_manager

logger = logging.getLogger(__name__)


async def check_voice_limit(user_id: int, duration: int):
    db = mongodb_manager.get_database(os.getenv("DB_NAME"))
    collection = db[os.getenv("COLLECTION_NAME")]
    result = await collection.find_one(
        {"user_id": user_id},
        {
            f"limits.{date.today()}.daily_seconds": 1,
            "daily_audio_limit": 1,
        },
    )
    if result is None:
        result = {}
    daily_seconds = (
        result.get("limits", {}).get(f"{date.today()}", {}).get("daily_seconds", 0)
    )
    daily_audio_limit = result.get("daily_audio_limit", 300)
    # TODO handle split audio
    if daily_audio_limit - daily_seconds - duration < 0:
        raise Exception


@alru_cache
async def transcribe(
    voice: bytes, user_id: int, duration: int, language: str | None = None
) -> str:
    db = mongodb_manager.get_database(os.getenv("DB_NAME"))
    collection = db[os.getenv("COLLECTION_NAME")]
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
    try:
        os.remove(file_name)
    except OSError as ex:
        logger.error(ex)
    await collection.update_one(
        {"user_id": user_id},
        {"$inc": {f"limits.{date.today()}.daily_seconds": duration}},
        upsert=True,
    )
    return result.get("text").strip()


async def transcribe_and_check(
    downloaded_file: bytes,
    user_id: int,
    duration: int,
):
    db = mongodb_manager.get_database(os.getenv("DB_NAME"))
    collection = db[os.getenv("COLLECTION_NAME")]
    # TODO set daily limit
    transcript = None
    try:
        # TODO handle date.fromtimestamp(msg_date) everywhere
        await check_voice_limit(user_id, duration)

        result = await collection.find_one(
            {"user_id": user_id},
            {"language": 1},
        )

        if result is None:
            result = {}

        transcript = await transcribe(
            bytes(downloaded_file),
            user_id,
            duration,
            result.get("language"),
        )

        messages = [
            SystemMessage(
                content="""Please review and edit the following text generated by an ASR system.
                    Ensure that the content, style, and language remain unchanged,
                    but correct any errors to make it more readable and coherent.
                    Do not add preambles to the edited paragraph or quotes surrounding your responses. Just give
                    me the edited text."""
            ),
            HumanMessage(content=transcript),
        ]

        transcript = await azure_openai_chat(messages)
    except Exception as ex:
        logger.error(ex)
    return transcript
