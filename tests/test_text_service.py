import sqlite3
import unittest

from telegram_llm_bot.bots.base_chatbot.services.text import user_error_message


class TextServiceErrorTest(unittest.TestCase):
    def test_maps_ollama_connection_error(self):
        text = user_error_message(RuntimeError("Could not connect to Ollama at http://x"))

        self.assertIn("Ollama is not running", text)

    def test_maps_missing_ollama_model(self):
        text = user_error_message(RuntimeError("Ollama model not found: qwen2.5:0.5b"))

        self.assertIn("Ollama model not found", text)
        self.assertIn("qwen2.5:0.5b", text)

    def test_maps_sqlite_error(self):
        text = user_error_message(sqlite3.OperationalError("unable to open database file"))

        self.assertIn("SQLITE_HISTORY_PATH", text)


if __name__ == "__main__":
    unittest.main()
