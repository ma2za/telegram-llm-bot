import logging
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from telegram_smart_bots.bots.voice_journal.services.text import (
    add_text,
    discard_text,
    history,
)
from telegram_smart_bots.bots.voice_journal.services.voice import set_openai_editor
from telegram_smart_bots.shared.utils import async_typing

logger = logging.getLogger(__name__)


@async_typing
async def discard_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    msg_date = datetime.fromtimestamp(
        float(update.message.reply_to_message.text.split(":=")[0].strip())
    )
    reply_msg = await discard_text(user_id, msg_date)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=reply_msg,
        reply_to_message_id=update.message.id,
    )


@async_typing
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if ":=" in text:
        msg_date = datetime.fromtimestamp(float(text.split(":=")[0].strip()))
        text = text.split(":=")[-1].strip()
    else:
        msg_date = update.message.forward_date
        if msg_date is None:
            msg_date = update.message.date
    user_id = update.message.from_user.id
    reply_msg = await add_text(user_id, msg_date, text)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=reply_msg,
        reply_to_message_id=update.message.id,
    )


@async_typing
async def history_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    msg_date = (
        str(datetime.strptime(context.args[0].strip(), "%Y-%m-%d").date())
        if len(context.args) == 1
        else None
    )
    messages = await history(user_id, msg_date)
    for reply_msg in messages:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=reply_msg,
            reply_to_message_id=update.message.id,
        )


@async_typing
async def editor_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_msg = await set_openai_editor(
        update.message.from_user.id,
        context.args[0] if len(context.args) == 1 else None,
        update.message.reply_to_message.text
        if update.message.reply_to_message is not None
        else None,
    )

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=reply_msg,
        reply_to_message_id=update.message.id,
    )
