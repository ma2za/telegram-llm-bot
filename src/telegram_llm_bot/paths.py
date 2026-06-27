from pathlib import Path

from dotenv import load_dotenv

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PACKAGE_DIR.parents[1]
BASE_CHATBOT_DIR = PACKAGE_DIR / "bots" / "base_chatbot"
LOGGING_CONFIG = PROJECT_DIR / "logging.conf"
LOG_DIR = PACKAGE_DIR / "logs"


def load_environment():
    load_dotenv(PROJECT_DIR / ".env")
    load_dotenv(BASE_CHATBOT_DIR / ".env")
