import logging
import os
from datetime import date

from langchain.schema import HumanMessage

from telegram_smart_bots.shared.history.history import MongoDBChatMessageHistory

logger = logging.getLogger(__name__)


async def add_text(user_id: int, msg_date: int, text: str):
    try:
        chat_history = MongoDBChatMessageHistory(
            os.getenv("DB_NAME"), user_id, f"{date.fromtimestamp(msg_date)}", "messages"
        )
        response = HumanMessage(content=text)
        response.additional_kwargs["timestamp"] = msg_date
        await chat_history.add_message(response)

        reply_msg = f"{msg_date}:={text}"
    except Exception as ex:
        logger.error(ex)
        reply_msg = "😿"
    return reply_msg
