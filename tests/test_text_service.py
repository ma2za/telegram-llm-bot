import asyncio
import sqlite3
import os
import unittest
from datetime import datetime
from unittest.mock import AsyncMock, patch

from telegram_llm_bot.bots.base_chatbot.services.text import (
    session_locks,
    text_chat_service,
    user_error_message,
)
from telegram_llm_bot.shared.history.history import (
    InMemoryChatMessageHistory,
    get_chat_history,
    set_active_session,
)


class TextServiceErrorTest(unittest.TestCase):
    def test_maps_ollama_connection_error(self):
        text = user_error_message(RuntimeError("Could not connect to Ollama at http://x"))

        self.assertIn("Ollama is not running", text)

    def test_maps_missing_ollama_model(self):
        text = user_error_message(RuntimeError("Ollama model not found: qwen3.5:0.8b"))

        self.assertIn("Ollama model not found", text)
        self.assertIn("qwen3.5:0.8b", text)

    def test_maps_sqlite_error(self):
        text = user_error_message(sqlite3.OperationalError("unable to open database file"))

        self.assertIn("SQLITE_HISTORY_PATH", text)


class TextServiceSessionTest(unittest.IsolatedAsyncioTestCase):
    async def test_writes_to_active_session(self):
        InMemoryChatMessageHistory.histories.clear()
        session_locks.clear()
        with patch.dict(
            os.environ,
            {
                "BOT_NAME": "bot",
                "CHAT_HISTORY_BACKEND": "memory",
            },
            clear=False,
        ):
            await set_active_session("bot", 1, "work")
            with patch(
                "telegram_llm_bot.bots.base_chatbot.services.text.chat",
                new=AsyncMock(return_value="response"),
            ):
                await text_chat_service(1, "hello", datetime(2026, 1, 1))

            work = get_chat_history("bot", 1, "work")
            default = get_chat_history("bot", 1, "default")
            work_messages = [message async for _, values in work.messages for message in values]
            default_messages = [
                message async for _, values in default.messages for message in values
            ]

        self.assertEqual([message.content for message in work_messages[-2:]], ["hello", "response"])
        self.assertEqual(default_messages, [])

    async def test_serializes_concurrent_messages_in_same_session(self):
        InMemoryChatMessageHistory.histories.clear()
        session_locks.clear()
        chat_calls = []

        async def delayed_chat(messages):
            chat_calls.append([message.content for message in messages])
            await asyncio.sleep(0.01)
            return f"response {messages[-1].content}"

        with patch.dict(
            os.environ,
            {
                "BOT_NAME": "bot",
                "CHAT_HISTORY_BACKEND": "memory",
            },
            clear=False,
        ):
            await set_active_session("bot", 1, "work")
            with patch("telegram_llm_bot.bots.base_chatbot.services.text.chat", new=delayed_chat):
                first = asyncio.create_task(
                    text_chat_service(1, "first", datetime(2026, 1, 1, 0, 0, 1))
                )
                await asyncio.sleep(0)
                second = asyncio.create_task(
                    text_chat_service(1, "second", datetime(2026, 1, 1, 0, 0, 2))
                )
                replies = await asyncio.gather(first, second)

            history = get_chat_history("bot", 1, "work")
            messages = [message async for _, values in history.messages for message in values]

        self.assertEqual(replies, ["response first", "response second"])
        self.assertEqual(chat_calls[0][-1], "first")
        self.assertIn("first", chat_calls[1])
        self.assertIn("response first", chat_calls[1])
        self.assertEqual(
            [message.content for message in messages[-4:]],
            ["first", "response first", "second", "response second"],
        )


if __name__ == "__main__":
    unittest.main()
