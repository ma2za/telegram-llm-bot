import logging
import os
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from telegram_smart_bots.bots.voice_journal.services.text import add_text, discard_text
from telegram_smart_bots.bots.voice_journal.services.voice import set_openai_editor
from telegram_smart_bots.shared.history.history import MongoDBChatMessageHistory
from telegram_smart_bots.shared.utils import async_typing

logger = logging.getLogger(__name__)


@async_typing
async def modify_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    msg_date = datetime.strptime(
        update.message.reply_to_message.text.split(":=")[0].strip(), "%Y-%m-%d"
    )
    new_text = update.message.text.split(":=")[-1].strip()
    reply_msg = await add_text(user_id, msg_date, new_text)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=reply_msg,
        reply_to_message_id=update.message.id,
    )


@async_typing
async def discard_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    msg_date = datetime.strptime(
        update.message.reply_to_message.text.split(":=")[0].strip(), "%Y-%m-%d"
    )
    msg_reply = await discard_text(user_id, msg_date)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=msg_reply,
        reply_to_message_id=update.message.id,
    )


@async_typing
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_date = update.message.date
    forward_date = update.message.forward_date
    user_id = update.message.from_user.id
    msg_date = message_date if forward_date is None else forward_date
    text = update.message.text

    reply_msg = await add_text(user_id, msg_date, text)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=reply_msg,
        reply_to_message_id=update.message.id,
    )


@async_typing
async def history_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    try:
        chat_history = MongoDBChatMessageHistory(
            os.getenv("DB_NAME"), user_id, history_field="messages"
        )

        result = await chat_history.messages
        for _, jrnl_entry in result.get("journal").items():
            for msg_date, msg in jrnl_entry.get("messages", {}).items():
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"{msg_date}:={msg}",
                    reply_to_message_id=update.message.id,
                )
    except ValueError as ex:
        logger.error(ex)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="😿",
            reply_to_message_id=update.message.id,
        )


@async_typing
async def editor_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_msg = await set_openai_editor(
        update.message.from_user.id,
        context.args[0] if len(context.args) == 1 else None,
        update.message.reply_to_message,
    )

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=reply_msg,
        reply_to_message_id=update.message.id,
    )
