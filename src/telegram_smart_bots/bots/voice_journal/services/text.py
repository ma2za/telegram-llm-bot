import logging
import os
from datetime import datetime

from langchain.schema import HumanMessage

from telegram_smart_bots.shared.history.history import MongoDBChatMessageHistory

logger = logging.getLogger(__name__)


async def add_text(user_id: int, msg_date: datetime, text: str):
    try:
        chat_history = MongoDBChatMessageHistory(
            os.getenv("BOT_NAME"), user_id, str(msg_date.date())
        )
        # await chat_history.clear()
        response = HumanMessage(content=text)
        response.additional_kwargs.update(
            {"timestamp": int(msg_date.timestamp()), "type": "text"}
        )
        await chat_history.add_message(response)

        reply_msg = f"{int(msg_date.timestamp())}:={text}"

    except Exception as ex:
        logger.error(ex)
        reply_msg = "😿"
    return reply_msg


async def discard_text(user_id: int, msg_date: datetime):
    try:
        chat_history = MongoDBChatMessageHistory(
            os.getenv("BOT_NAME"), user_id, f"{msg_date.date()}"
        )
        await chat_history.remove_message(str(int(msg_date.timestamp())))
        msg_reply = "😄"
    except Exception as ex:
        logger.error(ex)
        msg_reply = "😿"
    return msg_reply


async def history(user_id: int, msg_date: str = None):
    try:
        chat_history = MongoDBChatMessageHistory(
            os.getenv("BOT_NAME"), user_id, session_id=msg_date
        )
        messages = [
            f"{msg.additional_kwargs.get('timestamp')}:={msg.content}"
            async for k, v in chat_history.messages
            for msg in v
        ]
    except ValueError as ex:
        logger.error(ex)
        messages = ["😿"]
    return messages
