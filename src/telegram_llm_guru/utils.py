import asyncio

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes


async def typing_loop(
    update: Update, context: ContextTypes.DEFAULT_TYPE, sleep_interval: int = 1
):
    while context.user_data[update.update_id] is None:
        await update.message.chat.send_action(ChatAction.TYPING)
        await asyncio.sleep(sleep_interval)
