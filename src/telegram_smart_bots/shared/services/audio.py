import logging
import os

from telegram_smart_bots.shared.db.mongo import mongodb_manager

logger = logging.getLogger(__name__)


async def set_daily_audio_limit(user_id, daily_audio_limit):
    db = mongodb_manager.get_database(os.getenv("DB_NAME"))
    collection = db[os.getenv("COLLECTION_NAME")]

    try:
        await collection.update_one(
            {"telegram_id": user_id},
            {"$set": {"daily_audio_limit": daily_audio_limit}},
            upsert=True,
        )

        reply_msg = f"New daily limit for user {user_id}: {daily_audio_limit}"
    except Exception as ex:
        logger.error(ex)
        reply_msg = "😿"
    return reply_msg