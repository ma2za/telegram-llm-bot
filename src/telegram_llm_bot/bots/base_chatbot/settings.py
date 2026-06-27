import logging
from pathlib import Path
from typing import List, Dict, Any

import yaml
from telegram.ext import MessageHandler, filters, BaseHandler

from telegram_llm_bot.paths import BASE_CHATBOT_DIR, load_environment

load_environment()

from telegram_llm_bot.bots.base_chatbot.handlers.text import text_chat_handler

logger = logging.getLogger(__name__)


# TODO maybe move to config
class Settings:
    def __init__(self, config_file: Path, **values: Any):
        self.handlers: List[BaseHandler] = [
            MessageHandler(filters.TEXT, text_chat_handler, block=False),
        ]
        self.commands: Dict[str, str] = {}
        with open(config_file, "r") as f:
            config = yaml.safe_load(f)
        self.system_prompt = config.get("system") or ""
        self.start_message = config.get("start") or ""


settings = Settings(BASE_CHATBOT_DIR / "config.yml")
