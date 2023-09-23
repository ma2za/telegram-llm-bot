import logging
import os

from telegram import Update
from telegram.ext import ContextTypes

from telegram_smart_bots.shared.services.audio import set_daily_audio_limit
from telegram_smart_bots.shared.utils import async_typing

logger = logging.getLogger(__name__)


@async_typing
async def daily_audio_limit_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # TODO setup auth and context validation
    if update.message.from_user.id != int(os.getenv("ADMIN_ID")):
        raise Exception
    reply_msg = await set_daily_audio_limit(
        int(context.args[1]), float(context.args[0])
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=reply_msg,
        reply_to_message_id=update.message.id,
    )
