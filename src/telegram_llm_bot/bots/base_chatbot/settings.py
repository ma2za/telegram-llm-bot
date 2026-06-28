import logging
from typing import List, Dict, Any

from telegram.ext import MessageHandler, filters, BaseHandler

from telegram_llm_bot.config import load_bot_config
from telegram_llm_bot.paths import load_environment

load_environment()

from telegram_llm_bot.bots.base_chatbot.handlers.text import text_chat_handler
from telegram_llm_bot.bots.base_chatbot.handlers.voice import note_handler

logger = logging.getLogger(__name__)


# TODO maybe move to config
class Settings:
    def __init__(self, **values: Any):
        self.handlers: List[BaseHandler] = [
            MessageHandler(filters.TEXT, text_chat_handler, block=False),
            MessageHandler(filters.VOICE, note_handler, block=False),
        ]
        self.commands: Dict[str, str] = {}
        config = load_bot_config()
        self.config_file = config.path
        self.system_prompt = config.system
        self.start_message = config.start


settings = Settings()
