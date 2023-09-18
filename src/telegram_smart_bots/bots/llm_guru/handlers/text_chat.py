import logging

from telegram import Update
from telegram.ext import ContextTypes

from telegram_smart_bots.bots.llm_guru.services.text_chat import text_chat_service
from telegram_smart_bots.shared.utils import async_typing

logger = logging.getLogger(__name__)


@async_typing
async def text_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg_reply = await text_chat_service(
        update.message.from_user.id, update.message.text
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=msg_reply,
        reply_to_message_id=update.message.id,
    )
