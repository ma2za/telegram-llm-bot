import importlib
import logging
import os
from datetime import datetime

from langchain.schema import AIMessage, SystemMessage, HumanMessage

from telegram_llm_bot.shared.chat import beam_chat
from telegram_llm_bot.shared.history.history import MongoDBChatMessageHistory

settings = importlib.import_module(os.getenv("SETTINGS_FILE"))

logger = logging.getLogger(__name__)


async def text_chat_service(user_id: int, text: str, msg_date: datetime):
    try:
        chat_history = MongoDBChatMessageHistory(os.getenv("BOT_NAME"), user_id)
        # await chat_history.clear()

        messages = [msg async for k, v in chat_history.messages for msg in v]
        new_messages = []
        if not messages:
            new_messages.append(
                SystemMessage(
                    content=settings.settings.system_prompt,
                    additional_kwargs={
                        "type": "system",
                        "timestamp": int(msg_date.timestamp()) - 10,
                    },
                )
            )
        new_messages.append(
            HumanMessage(
                content=text,
                additional_kwargs={
                    "type": "text",
                    "timestamp": int(msg_date.timestamp()),
                },
            )
        )
        response = await beam_chat(
            {
                "messages": list(
                    chat_history.messages_to_dict(messages + new_messages).values()
                )
            }
        )
        new_messages.append(
            AIMessage(
                content=response,
                additional_kwargs={
                    "type": "text",
                    "timestamp": int(msg_date.timestamp()) + 10,
                },
            )
        )
        await chat_history.add_messages(new_messages)

        reply_msg = response
    except Exception as ex:
        logger.error(ex)
        reply_msg = "😿"
    return reply_msg
