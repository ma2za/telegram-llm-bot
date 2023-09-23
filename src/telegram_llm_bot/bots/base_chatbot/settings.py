import logging
from typing import List, Dict, Any

import yaml
from pydantic_settings import BaseSettings
from telegram.ext import MessageHandler, filters, BaseHandler

from telegram_llm_bot.bots.base_chatbot.handlers.text import text_chat_handler

logger = logging.getLogger(__name__)


# TODO maybe move to config
class Settings(BaseSettings):
    handlers: List[BaseHandler] = [
        MessageHandler(filters.TEXT, text_chat_handler, block=False),
        # MessageHandler(filters.VOICE, note_handler, block=False),
        # CommandHandler("note", switch_handler, block=False),
        # CommandHandler("summarize", summarize_handler, block=False),
        # CommandHandler("audio_limit", daily_audio_limit_handler, block=False),
    ]

    commands: Dict[str, str] = {
        # "note": "note name (no spaces)",
        # "summarize": "summarize current conversation",
    }
    system_prompt: str = ""
    start_message: str = ""

    def __init__(self, config_file: str, **values: Any):
        super().__init__(**values)
        with open(config_file, "r") as f:
            config = yaml.load(f, Loader=yaml.Loader)
        Settings.system_prompt = config.get("system")
        Settings.start_message = config.get("start")


settings = Settings("bots/base_chatbot/config.yml")
