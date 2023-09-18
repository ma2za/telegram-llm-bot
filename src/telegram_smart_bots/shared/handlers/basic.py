import logging

from telegram import Update
from telegram.ext import ContextTypes

from telegram_smart_bots.shared.utils import async_typing

logger = logging.getLogger(__name__)


@async_typing
async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Hello!!! I am your personal voice journal! 😄",
        reply_to_message_id=update.message.id,
    )


@async_typing
async def handle_telegram_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=update.message.from_user.id,
        reply_to_message_id=update.message.id,
    )
