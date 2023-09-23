import logging

from telegram import Update
from telegram.ext import ContextTypes

from telegram_llm_bot.bots.idea_sparring.services.ideas import (
    idea_chat,
    summarize,
    switch,
)
from telegram_llm_bot.shared.utils import async_typing

logger = logging.getLogger(__name__)


@async_typing
async def idea_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_info = await update.message.voice.get_file()
    downloaded_file = await file_info.download_as_bytearray()

    reply_msg = await idea_chat(
        downloaded_file, update.message.from_user.id, update.message.voice.duration
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=reply_msg,
        reply_to_message_id=update.message.id,
    )


@async_typing
async def switch_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_msg = await switch(update.message.from_user.id, context.args[0])
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=reply_msg,
        reply_to_message_id=update.message.id,
    )


@async_typing
async def summarize_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_msg = await summarize(update.message.from_user.id)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=reply_msg,
        reply_to_message_id=update.message.id,
    )
