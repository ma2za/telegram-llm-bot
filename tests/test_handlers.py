import os
import tempfile
import unittest
from unittest.mock import patch

from telegram_llm_bot.shared.handlers.basic import (
    delete_session_text,
    health_text,
    help_text,
    model_status_text,
    new_session_text,
    session_text,
    sessions_text,
    settings_text,
    use_session_text,
)


class ModelStatusTest(unittest.IsolatedAsyncioTestCase):
    def test_model_status_excludes_secrets(self):
        with patch.dict(
            os.environ,
            {
                "LLM_PROVIDER": "ollama",
                "OLLAMA_MODEL": "qwen2.5:0.5b",
                "OLLAMA_BASE_URL": "http://user:secret@localhost:11434",
                "BEAM_TOKEN": "secret-token",
                "CHAT_HISTORY_BACKEND": "sqlite",
            },
            clear=False,
        ):
            text = model_status_text()

        self.assertIn("Provider: ollama", text)
        self.assertIn("Model: qwen2.5:0.5b", text)
        self.assertIn("History: sqlite", text)
        self.assertIn("Context: 1024", text)
        self.assertNotIn("secret", text)
        self.assertNotIn("localhost", text)

    def test_help_lists_core_commands(self):
        text = help_text()

        self.assertIn("/help", text)
        self.assertIn("/health", text)
        self.assertIn("/settings", text)
        self.assertIn("/reset", text)
        self.assertIn("/session", text)
        self.assertIn("/new", text)

    async def test_settings_excludes_secrets(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(
                os.environ,
                {
                    "BOT_NAME": "telegram-llm-bot",
                    "LLM_PROVIDER": "ollama",
                    "OLLAMA_MODEL": "qwen2.5:0.5b",
                    "OLLAMA_BASE_URL": "http://user:secret@localhost:11434",
                    "TELEGRAM_BOT_TOKEN": "secret-token",
                    "CHAT_HISTORY_BACKEND": "sqlite",
                    "SQLITE_HISTORY_PATH": f"{directory}/history.sqlite3",
                },
                clear=False,
            ):
                text = await settings_text(1)

        self.assertIn("Bot: telegram-llm-bot", text)
        self.assertIn("Provider: ollama", text)
        self.assertIn("Session: default", text)
        self.assertNotIn("secret", text)
        self.assertNotIn("localhost", text)

    async def test_health_excludes_secrets(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(
                os.environ,
                {
                    "BOT_NAME": "telegram-llm-bot",
                    "LLM_PROVIDER": "ollama",
                    "OLLAMA_MODEL": "qwen2.5:0.5b",
                    "OLLAMA_BASE_URL": "http://user:secret@localhost:11434",
                    "TELEGRAM_BOT_TOKEN": "secret-token",
                    "CHAT_HISTORY_BACKEND": "sqlite",
                    "SQLITE_HISTORY_PATH": f"{directory}/history.sqlite3",
                },
                clear=False,
            ):
                text = await health_text(1)

        self.assertIn("Status: ok", text)
        self.assertIn("Provider: ollama", text)
        self.assertIn("Model: qwen2.5:0.5b", text)
        self.assertIn("History: sqlite", text)
        self.assertIn("Session: default", text)
        self.assertIn("SQLite path writable: yes", text)
        self.assertNotIn("secret", text)
        self.assertNotIn("localhost", text)


class SessionCommandTextTest(unittest.IsolatedAsyncioTestCase):
    async def test_session_commands(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(
                os.environ,
                {
                    "BOT_NAME": "telegram-llm-bot",
                    "CHAT_HISTORY_BACKEND": "sqlite",
                    "SQLITE_HISTORY_PATH": f"{directory}/history.sqlite3",
                },
                clear=False,
            ):
                self.assertEqual(await session_text(1), "Current session: default")
                self.assertEqual(await new_session_text(1, ["work"]), "Current session: work")
                self.assertIn("* work", await sessions_text(1))
                self.assertEqual(await use_session_text(1, ["work"]), "Current session: work")
                self.assertEqual(await delete_session_text(1, ["work"]), "Deleted session: work")
                self.assertEqual(await use_session_text(1, ["work"]), "Session not found: work")


if __name__ == "__main__":
    unittest.main()
