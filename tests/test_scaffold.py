import tempfile
import unittest
from pathlib import Path

from telegram_llm_bot.scaffold import init_project


class ScaffoldTest(unittest.TestCase):
    def test_creates_starter_files(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)

            files = init_project(target)

            self.assertEqual(
                files,
                [target / ".env", target / "bot.env", target / "bot.yml"],
            )
            self.assertTrue((target / ".env").exists())
            self.assertIn("LLM_PROVIDER=ollama", (target / ".env").read_text(encoding="utf-8"))
            self.assertIn(
                "BOT_CONFIG_FILE=bot.yml",
                (target / "bot.env").read_text(encoding="utf-8"),
            )
            self.assertIn("system:", (target / "bot.yml").read_text(encoding="utf-8"))

    def test_refuses_overwrite_without_force(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            init_project(target)

            with self.assertRaises(FileExistsError):
                init_project(target)

    def test_overwrites_with_force(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            init_project(target)
            (target / "bot.yml").write_text("changed: true\n", encoding="utf-8")

            init_project(target, force=True)

            self.assertIn("start:", (target / "bot.yml").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
