import os
import unittest
from unittest.mock import patch

from telegram_llm_bot.shared.handlers.basic import help_text, model_status_text, settings_text


class ModelStatusTest(unittest.TestCase):
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
        self.assertIn("/settings", text)
        self.assertIn("/reset", text)

    def test_settings_excludes_secrets(self):
        with patch.dict(
            os.environ,
            {
                "BOT_NAME": "telegram-llm-bot",
                "LLM_PROVIDER": "ollama",
                "OLLAMA_MODEL": "qwen2.5:0.5b",
                "OLLAMA_BASE_URL": "http://user:secret@localhost:11434",
                "TELEGRAM_BOT_TOKEN": "secret-token",
                "CHAT_HISTORY_BACKEND": "sqlite",
            },
            clear=False,
        ):
            text = settings_text()

        self.assertIn("Bot: telegram-llm-bot", text)
        self.assertIn("Provider: ollama", text)
        self.assertNotIn("secret", text)
        self.assertNotIn("localhost", text)


if __name__ == "__main__":
    unittest.main()
