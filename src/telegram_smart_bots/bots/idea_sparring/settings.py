import logging

from telegram.ext import MessageHandler, filters, CommandHandler

logger = logging.getLogger(__name__)


class Settings:
    handlers = [
        MessageHandler(filters.VOICE, handle_voice, block=False),
        CommandHandler("idea", handle_idea, block=False),
        CommandHandler("summarize", handle_idea_summarize, block=False),
    ]
