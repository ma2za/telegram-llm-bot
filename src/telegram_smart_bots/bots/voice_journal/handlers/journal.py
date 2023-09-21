import logging
import os
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from telegram_smart_bots.bots.voice_journal.utils.journal import write
from telegram_smart_bots.shared.history.history import MongoDBChatMessageHistory
from telegram_smart_bots.shared.utils import async_typing

logger = logging.getLogger(__name__)


@async_typing
async def journal_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    msg_date = (
        str(datetime.strptime(context.args[0].strip(), "%Y-%m-%d").date())
        if len(context.args) == 1
        else None
    )

    journal_file = f".tmp/journal_{user_id}.pdf"
    try:
        chat_history = MongoDBChatMessageHistory(
            os.getenv("BOT_NAME"), user_id, session_id=msg_date
        )
        await write(journal_file, chat_history.messages, user_id)

        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=open(journal_file, "rb"),
            write_timeout=180,
        )
    except ValueError as ex:
        logger.error(ex)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="😿",
            reply_to_message_id=update.message.id,
        )
    except Exception as ex:
        logger.error(ex)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="😿",
            reply_to_message_id=update.message.id,
        )
    finally:
        if os.path.exists(journal_file):
            try:
                os.remove(journal_file)
            except OSError as e:
                print(f"Error: {e}")
        context.user_data[update.update_id] = "Done"
