import logging
import os

from telegram_smart_bots.shared.db.mongo import mongodb_manager

logger = logging.getLogger(__name__)


async def set_language(user_id, language):
    db = mongodb_manager.get_database(os.getenv("DB_NAME"))
    collection = db[os.getenv("COLLECTION_NAME")]

    try:
        await collection.update_one(
            {"telegram_id": user_id},
            {"$set": {"language": language}},
            upsert=True,
        )

        reply_msg = f"Switched to language: {language}"
    except Exception as ex:
        logger.error(ex)
        reply_msg = "😿"
    return reply_msg
