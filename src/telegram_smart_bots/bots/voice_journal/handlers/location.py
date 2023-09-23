import logging

from telegram import Update
from telegram.ext import ContextTypes

from telegram_smart_bots.bots.voice_journal.services.location import add_location
from telegram_smart_bots.shared.utils import async_typing

logger = logging.getLogger(__name__)


@async_typing
async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    forward_date = update.message.forward_date
    msg_date = update.message.date if forward_date is None else forward_date
    user_id = update.message.from_user.id
    latitude = update.message.location.latitude
    longitude = update.message.location.longitude
    reply_msg = await add_location(user_id, msg_date, latitude, longitude)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=reply_msg,
        reply_to_message_id=update.message.id,
    )
