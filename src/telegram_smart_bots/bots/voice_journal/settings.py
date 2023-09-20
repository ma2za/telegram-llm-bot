import logging
from typing import List, Dict

from pydantic_settings import BaseSettings
from telegram.ext import MessageHandler, filters, BaseHandler, CommandHandler

from telegram_smart_bots.bots.voice_journal.handlers.journal import journal_handler
from telegram_smart_bots.bots.voice_journal.handlers.location import location_handler
from telegram_smart_bots.bots.voice_journal.handlers.text import (
    text_handler,
    editor_handler,
    discard_text_handler,
    history_handler,
)
from telegram_smart_bots.bots.voice_journal.handlers.voice import voice_handler
from telegram_smart_bots.shared.handlers.audio import daily_audio_limit_handler

logger = logging.getLogger(__name__)


# TODO maybe move to config
class Settings(BaseSettings):
    handlers: List[BaseHandler] = [
        MessageHandler(filters.LOCATION, location_handler, block=False),
        MessageHandler(filters.VOICE, voice_handler, block=False),
        # MessageHandler(filters.PHOTO, handle_photo, block=False),
        CommandHandler("history", history_handler, block=False),
        CommandHandler("discard", discard_text_handler, block=False),
        CommandHandler("journal", journal_handler, block=False),
        CommandHandler("editor", editor_handler, block=False),
        CommandHandler("audio_limit", daily_audio_limit_handler, block=False),
        MessageHandler(filters.TEXT, text_handler, block=False),
    ]

    commands: Dict[str, str] = {
        "journal": "journal (opt) YYYY-MM-DD",
        "discard": "discard",
        "editor": "editor (opt) 0-1 or -1 to unset",
        "history": "history (opt) YYYY-MM-DD",
    }

    start_message: str = "Hello!!! I am your personal voice journal! 😄"


settings = Settings()
