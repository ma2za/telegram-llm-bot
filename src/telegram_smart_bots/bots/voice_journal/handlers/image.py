import logging
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from telegram_smart_bots.bots.voice_journal.services.image import add_image
from telegram_smart_bots.shared.utils import async_typing

logger = logging.getLogger(__name__)


@async_typing
async def image_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if update.message.caption is None:
        message_date = update.message.date
        forward_date = update.message.forward_date
        msg_date = message_date if forward_date is None else forward_date
    else:
        msg_date = datetime.strptime(update.message.caption.strip(), "%Y-%m-%d")
    photo_file = await update.message.photo[-1].get_file()
    downloaded_file = await photo_file.download_as_bytearray()
    reply_msg = await add_image(
        user_id, msg_date, photo_file.file_id, bytes(downloaded_file)
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=reply_msg,
        reply_to_message_id=update.message.id,
    )
