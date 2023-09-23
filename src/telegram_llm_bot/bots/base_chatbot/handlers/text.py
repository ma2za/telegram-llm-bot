import logging

from telegram import Update
from telegram.ext import ContextTypes

from telegram_llm_bot.bots.base_chatbot.services.text import text_chat_service
from telegram_llm_bot.shared.utils import async_typing

logger = logging.getLogger(__name__)


@async_typing
async def text_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_msg = await text_chat_service(
        update.message.from_user.id, update.message.text, update.message.date
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=reply_msg,
        reply_to_message_id=update.message.id,
    )
