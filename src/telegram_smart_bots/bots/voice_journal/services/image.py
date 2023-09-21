import datetime
import logging
import os

from langchain.schema import HumanMessage

from telegram_smart_bots.shared.db.minio_storage import minio_manager
from telegram_smart_bots.shared.history.history import MongoDBChatMessageHistory

logger = logging.getLogger(__name__)


async def add_image(
    user_id: int, msg_date: datetime.datetime, file_id: str, file_bytes: bytes
):
    try:
        history = MongoDBChatMessageHistory(
            os.getenv("BOT_NAME"), user_id, str(msg_date.date())
        )
        object_name = f"{user_id}/{str(msg_date.date())}/{file_id}.png"
        # TODO async
        # TODO remove old image
        await minio_manager.put_object(object_name, file_bytes)

        await history.add_message(
            HumanMessage(
                content=object_name,
                additional_kwargs={
                    "timestamp": int(msg_date.timestamp()),
                    "type": "image",
                },
            )
        )

        reply_msg = "😄"
    except Exception as ex:
        logger.error(ex)
        reply_msg = "😢"
    return reply_msg
