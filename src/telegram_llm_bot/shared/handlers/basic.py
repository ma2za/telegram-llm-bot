import importlib
import logging
import os

from telegram import Update
from telegram.ext import ContextTypes

from telegram_llm_bot.shared.services.basic import set_language
from telegram_llm_bot.shared.utils import async_typing

settings = importlib.import_module(os.getenv("SETTINGS_FILE"))

logger = logging.getLogger(__name__)


@async_typing
async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=settings.settings.start_message,
        reply_to_message_id=update.message.id,
    )


@async_typing
async def handle_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=update.message.from_user.id,
        reply_to_message_id=update.message.id,
    )


@async_typing
async def handle_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # TODO replace with pydantic
    if len(context.args) != 1:
        reply_msg = "😿"
    else:
        reply_msg = await set_language(update.message.from_user.id, context.args[0])
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=reply_msg,
        reply_to_message_id=update.message.id,
    )
