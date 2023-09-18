import logging
from typing import List, Dict

from pydantic_settings import BaseSettings
from telegram.ext import MessageHandler, filters, CommandHandler, BaseHandler

from telegram_smart_bots.bots.voice_journal.handlers.voice import voice_handler

logger = logging.getLogger(__name__)


# TODO maybe move to config
class Settings(BaseSettings):
    handlers: List[BaseHandler] = [
        MessageHandler(filters.LOCATION, handle_location, block=False),
        MessageHandler(filters.VOICE, voice_handler, block=False),
        MessageHandler(filters.PHOTO, handle_photo, block=False),
        CommandHandler("messages", handle_messages, block=False),
        CommandHandler("discard", handle_discard, block=False),
        CommandHandler("journal", handle_journal, block=False),
        CommandHandler("editor", handle_editor, block=False),
        CommandHandler("location", handle_location_text, block=False),
        MessageHandler(filters.TEXT & filters.REPLY, modify_message, block=False),
        MessageHandler(filters.TEXT, handle_message, block=False),
    ]

    commands: Dict[str, str] = {
        "journal": "journal (opt) YYYY-MM-DD",
        "discard": "discard",
        "location": "location PLACE (opt) YYYY-MM-DD",
        "editor": "editor (opt) 0-1 or -1 to unset",
        "messages": "messages (opt) YYYY-MM-DD",
    }

    start_message: str = "Hello!!! I am your personal voice journal! 😄"


settings = Settings()
