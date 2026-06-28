import asyncio
import importlib
import logging
import os
import sqlite3
from datetime import datetime

from telegram_llm_bot.shared.chat import chat
from telegram_llm_bot.shared.history.history import get_active_session, get_chat_history
from telegram_llm_bot.shared.messages import AIMessage, HumanMessage, SystemMessage

settings = importlib.import_module(
    os.getenv("SETTINGS_FILE", "telegram_llm_bot.bots.base_chatbot.settings")
)

logger = logging.getLogger(__name__)
session_locks = {}


def user_error_message(ex: Exception) -> str:
    text = str(ex)
    if "Could not connect to Ollama" in text:
        return "Ollama is not running or is unreachable. Start Ollama and try again."
    if "Ollama model not found" in text:
        return text
    if isinstance(ex, sqlite3.Error) or "unable to open database file" in text:
        return "Chat history storage is not writable. Check SQLITE_HISTORY_PATH."
    if "Unsupported LLM_PROVIDER" in text or "Set LLM_PROVIDER" in text:
        return "The LLM provider is not configured correctly."
    return "I could not generate a response. Check the bot logs for details."


def get_session_lock(bot_name: str, user_id: int, session_id: str):
    key = (bot_name, user_id, session_id)
    if key not in session_locks:
        session_locks[key] = asyncio.Lock()
    return session_locks[key]


async def text_chat_service(user_id: int, text: str, msg_date: datetime):
    try:
        bot_name = os.getenv("BOT_NAME")
        session_id = await get_active_session(bot_name, user_id)
        lock = get_session_lock(bot_name, user_id, session_id)
        async with lock:
            chat_history = get_chat_history(bot_name, user_id, session_id)

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
            response = await chat(messages + new_messages)
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

            reply_msg = response or "I could not generate a response."
    except Exception as ex:
        logger.exception(ex)
        reply_msg = user_error_message(ex)
    return reply_msg
