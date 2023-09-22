import logging
from typing import List, Dict

from pydantic_settings import BaseSettings
from telegram.ext import MessageHandler, filters, BaseHandler

from telegram_smart_bots.bots.llm_guru.handlers.text_chat import text_chat_handler

logger = logging.getLogger(__name__)


# TODO maybe move to config
class Settings(BaseSettings):
    handlers: List[BaseHandler] = [
        MessageHandler(filters.TEXT, text_chat_handler, block=False),
    ]

    commands: Dict[str, str] = {}

    start_message: str = "Hello!!! I am your personal travel guru! 😄"


settings = Settings()
