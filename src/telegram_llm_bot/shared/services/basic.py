import logging
import os

from telegram_llm_bot.shared.db.mongo import mongodb_manager

logger = logging.getLogger(__name__)


async def set_language(user_id, language):
    db = mongodb_manager.get_database(os.getenv("BOT_NAME"))
    collection = db[os.getenv("COLLECTION_NAME")]

    try:
        await collection.update_one(
            {"user_id": user_id},
            {"$set": {"language": language}},
            upsert=True,
        )

        reply_msg = f"Switched to language: {language}"
    except Exception as ex:
        logger.error(ex)
        reply_msg = "😿"
    return reply_msg
