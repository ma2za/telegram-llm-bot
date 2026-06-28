import logging

from telegram import Update
from telegram.ext import ContextTypes

from telegram_llm_bot.bots.base_chatbot.services.voice import new_note
from telegram_llm_bot.shared.utils import async_typing

logger = logging.getLogger(__name__)


@async_typing
async def note_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_info = await update.message.voice.get_file()
    downloaded_file = await file_info.download_as_bytearray()

    reply_msg = await new_note(
        bytes(downloaded_file),
        update.message.from_user.id,
        update.message.voice.duration,
        update.message.date,
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=reply_msg,
        reply_to_message_id=update.message.id,
    )
