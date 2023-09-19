import logging
import os
from datetime import datetime

from langchain.schema import HumanMessage

from telegram_smart_bots.shared.history.history import MongoDBChatMessageHistory

logger = logging.getLogger(__name__)


async def add_text(user_id: int, msg_date: datetime, text: str):
    try:
        chat_history = MongoDBChatMessageHistory(
            os.getenv("DB_NAME"), user_id, f"{msg_date.date()}", "messages"
        )
        response = HumanMessage(content=text)
        response.additional_kwargs["timestamp"] = int(msg_date.timestamp())
        await chat_history.add_message(response)

        reply_msg = f"{msg_date}:={text}"

    except Exception as ex:
        logger.error(ex)
        reply_msg = "😿"
    return reply_msg


async def discard_text(user_id: int, msg_date: datetime):
    try:
        chat_history = MongoDBChatMessageHistory(
            os.getenv("DB_NAME"), user_id, f"{msg_date.date()}", "messages"
        )
        await chat_history.remove_message(str(int(msg_date.timestamp())))
        msg_reply = "😄"
    except Exception as ex:
        logger.error(ex)
        msg_reply = "😿"
    return msg_reply
