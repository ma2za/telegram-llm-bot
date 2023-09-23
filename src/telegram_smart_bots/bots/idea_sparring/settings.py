import logging
from typing import List, Dict

from pydantic_settings import BaseSettings
from telegram.ext import MessageHandler, filters, CommandHandler, BaseHandler

from telegram_smart_bots.bots.idea_sparring.handlers.ideas import (
    idea_handler,
    switch_handler,
    summarize_handler,
)
from telegram_smart_bots.shared.handlers.audio import daily_audio_limit_handler

logger = logging.getLogger(__name__)


# TODO maybe move to config
class Settings(BaseSettings):
    handlers: List[BaseHandler] = [
        MessageHandler(filters.VOICE, idea_handler, block=False),
        CommandHandler("idea", switch_handler, block=False),
        CommandHandler("summarize", summarize_handler, block=False),
        CommandHandler("audio_limit", daily_audio_limit_handler, block=False),
    ]

    commands: Dict[str, str] = {
        "idea": "idea name (no spaces)",
        "summarize": "summarize current idea",
    }

    start_message: str = "Hello!!! I am your personal idea sparring partner! 😃"


settings = Settings()
