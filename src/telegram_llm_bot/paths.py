from pathlib import Path

from dotenv import load_dotenv

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PACKAGE_DIR.parents[1]
BASE_CHATBOT_DIR = PACKAGE_DIR / "bots" / "base_chatbot"
LOGGING_CONFIG = PROJECT_DIR / "logging.conf"
LOG_DIR = PACKAGE_DIR / "logs"
ROOT_ENV_FILE = PROJECT_DIR / ".env"
BOT_ENV_FILE = PROJECT_DIR / "bot.env"
BASE_CHATBOT_ENV_FILE = BASE_CHATBOT_DIR / ".env"


def environment_files():
    return [ROOT_ENV_FILE, BOT_ENV_FILE, BASE_CHATBOT_ENV_FILE]


def load_environment():
    for path in environment_files():
        load_dotenv(path)
