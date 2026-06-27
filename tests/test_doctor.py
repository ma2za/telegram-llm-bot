import contextlib
import io
import os
import tempfile
import unittest
from unittest.mock import patch

from telegram_llm_bot.doctor import doctor_async


class DoctorTest(unittest.IsolatedAsyncioTestCase):
    async def test_doctor_passes_with_dummy_token_without_live_checks(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(
                os.environ,
                {
                    "TELEGRAM_BOT_TOKEN": "123456:ci-dummy-token",
                    "SETTINGS_FILE": "telegram_llm_bot.bots.base_chatbot.settings",
                    "BOT_NAME": "telegram-llm-bot",
                    "LLM_PROVIDER": "ollama",
                    "OLLAMA_MODEL": "qwen2.5:0.5b",
                    "OLLAMA_NUM_CTX": "1024",
                    "OLLAMA_NUM_PREDICT": "256",
                    "OLLAMA_TEMPERATURE": "0.2",
                    "CHAT_HISTORY_BACKEND": "sqlite",
                    "SQLITE_HISTORY_PATH": f"{directory}/history.sqlite3",
                },
                clear=False,
            ):
                with contextlib.redirect_stdout(io.StringIO()):
                    code = await doctor_async(live=False)

        self.assertEqual(code, 0)

    async def test_doctor_fails_on_missing_provider(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(
                os.environ,
                {
                    "TELEGRAM_BOT_TOKEN": "123:abc",
                    "SETTINGS_FILE": "telegram_llm_bot.bots.base_chatbot.settings",
                    "BOT_NAME": "telegram-llm-bot",
                    "LLM_PROVIDER": "",
                    "CHAT_HISTORY_BACKEND": "sqlite",
                    "SQLITE_HISTORY_PATH": f"{directory}/history.sqlite3",
                },
                clear=False,
            ):
                with contextlib.redirect_stdout(io.StringIO()):
                    code = await doctor_async(live=False)

        self.assertEqual(code, 1)

    async def test_doctor_fails_on_empty_token(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(
                os.environ,
                {
                    "TELEGRAM_BOT_TOKEN": "",
                    "SETTINGS_FILE": "telegram_llm_bot.bots.base_chatbot.settings",
                    "BOT_NAME": "telegram-llm-bot",
                    "LLM_PROVIDER": "ollama",
                    "CHAT_HISTORY_BACKEND": "sqlite",
                    "SQLITE_HISTORY_PATH": f"{directory}/history.sqlite3",
                },
                clear=False,
            ):
                with contextlib.redirect_stdout(io.StringIO()):
                    code = await doctor_async(live=False)

        self.assertEqual(code, 1)

    async def test_doctor_fails_on_replace_me_token(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(
                os.environ,
                {
                    "TELEGRAM_BOT_TOKEN": "replace-me",
                    "SETTINGS_FILE": "telegram_llm_bot.bots.base_chatbot.settings",
                    "BOT_NAME": "telegram-llm-bot",
                    "LLM_PROVIDER": "ollama",
                    "CHAT_HISTORY_BACKEND": "sqlite",
                    "SQLITE_HISTORY_PATH": f"{directory}/history.sqlite3",
                },
                clear=False,
            ):
                with contextlib.redirect_stdout(io.StringIO()):
                    code = await doctor_async(live=False)

        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
