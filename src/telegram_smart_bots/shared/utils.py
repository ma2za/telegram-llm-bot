import asyncio
import logging

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def typing_loop(
    update: Update, context: ContextTypes.DEFAULT_TYPE, sleep_interval: int = 1
):
    while context.user_data[update.update_id] is None:
        await update.message.chat.send_action(ChatAction.TYPING)
        await asyncio.sleep(sleep_interval)


def async_typing(op):
    async def inner(update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data[update.update_id] = None
        typing_task = asyncio.create_task(typing_loop(update, context))
        await asyncio.sleep(0.1)
        handler_task = asyncio.create_task(op(update, context))
        await handler_task
        context.user_data[update.update_id] = "Done"
        await typing_task
        del context.user_data[update.update_id]

    return inner
