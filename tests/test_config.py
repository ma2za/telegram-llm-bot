import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from telegram_llm_bot.config import DEFAULT_BOT_CONFIG_FILE, bot_config_path, load_bot_config


class ConfigTest(unittest.TestCase):
    def test_uses_bot_config_file_when_set(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bot.yml"
            path.write_text("start: Hi\nsystem: Be useful.\n", encoding="utf-8")

            with patch.dict(os.environ, {"BOT_CONFIG_FILE": str(path)}, clear=False):
                config = load_bot_config()

        self.assertEqual(config.path, path)
        self.assertEqual(config.start, "Hi")
        self.assertEqual(config.system, "Be useful.")

    def test_falls_back_to_bundled_config(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(bot_config_path(), DEFAULT_BOT_CONFIG_FILE)

    def test_requires_start_and_system(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bot.yml"
            path.write_text("start: Hi\n", encoding="utf-8")

            with patch.dict(os.environ, {"BOT_CONFIG_FILE": str(path)}, clear=False):
                with self.assertRaisesRegex(ValueError, "start and system"):
                    load_bot_config()


if __name__ == "__main__":
    unittest.main()
