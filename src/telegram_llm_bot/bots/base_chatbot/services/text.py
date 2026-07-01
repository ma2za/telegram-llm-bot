import asyncio
import importlib
import logging
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime

from telegram_llm_bot.shared.chat import chat
from telegram_llm_bot.shared.history.history import get_active_session, get_chat_history
from telegram_llm_bot.shared.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

settings = importlib.import_module(
    os.getenv("SETTINGS_FILE", "telegram_llm_bot.bots.base_chatbot.settings")
)

logger = logging.getLogger(__name__)
session_locks = {}
DEFAULT_CHAT_HISTORY_MAX_MESSAGES = 20


@dataclass
class TextChatMessages:
    provider_messages: list[BaseMessage]
    new_messages: list[BaseMessage]


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


def chat_history_max_messages() -> int:
    return max(0, int(os.getenv("CHAT_HISTORY_MAX_MESSAGES", DEFAULT_CHAT_HISTORY_MAX_MESSAGES)))


def provider_history_messages(messages: list[BaseMessage]) -> list[BaseMessage]:
    system_messages = [message for message in messages if message.type == "system"]
    conversation_messages = [message for message in messages if message.type != "system"]
    limit = chat_history_max_messages()
    if limit:
        conversation_messages = conversation_messages[-limit:]
    else:
        conversation_messages = []
    return system_messages[:1] + conversation_messages


def build_text_chat_messages(
    history_messages: list[BaseMessage], text: str, msg_date: datetime
) -> TextChatMessages:
    provider_messages = provider_history_messages(history_messages)
    timestamp = int(msg_date.timestamp())
    new_messages = []
    if not any(message.type == "system" for message in provider_messages):
        new_messages.append(
            SystemMessage(
                content=settings.settings.system_prompt,
                additional_kwargs={
                    "type": "system",
                    "timestamp": timestamp - 10,
                },
            )
        )
    new_messages.append(
        HumanMessage(
            content=text,
            additional_kwargs={
                "type": "text",
                "timestamp": timestamp,
            },
        )
    )
    return TextChatMessages(provider_messages + new_messages, new_messages)


async def text_chat_service(user_id: int, text: str, msg_date: datetime):
    try:
        bot_name = os.getenv("BOT_NAME")
        session_id = await get_active_session(bot_name, user_id)
        lock = get_session_lock(bot_name, user_id, session_id)
        async with lock:
            chat_history = get_chat_history(bot_name, user_id, session_id)

            messages = [msg async for k, v in chat_history.messages for msg in v]
            chat_messages = build_text_chat_messages(messages, text, msg_date)
            response = str(await chat(chat_messages.provider_messages) or "").strip()
            reply_msg = response or "I could not generate a response."
            chat_messages.new_messages.append(
                AIMessage(
                    content=reply_msg,
                    additional_kwargs={
                        "type": "text",
                        "timestamp": int(msg_date.timestamp()) + 10,
                    },
                )
            )
            await chat_history.add_messages(chat_messages.new_messages)
    except Exception as ex:
        logger.exception(ex)
        reply_msg = user_error_message(ex)
    return reply_msg
