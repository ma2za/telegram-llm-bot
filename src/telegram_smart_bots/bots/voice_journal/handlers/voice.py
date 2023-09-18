import logging

from telegram import Update
from telegram.ext import ContextTypes

from telegram_smart_bots.bots.voice_journal.services.voice import voice_chat
from telegram_smart_bots.shared.utils import async_typing

logger = logging.getLogger(__name__)


@async_typing
async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_info = await update.message.voice.get_file()
    downloaded_file = await file_info.download_as_bytearray()
    message_date = update.message.date
    forward_date = update.message.forward_date

    msg_date = message_date if forward_date is None else forward_date
    msg_date = int(msg_date.timestamp())

    reply_msg = await voice_chat(
        downloaded_file,
        update.message.from_user.id,
        update.message.voice.duration,
        msg_date,
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=reply_msg,
        reply_to_message_id=update.message.id,
    )
