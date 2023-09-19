import logging
import os
from datetime import date

from telegram import Update
from telegram.ext import ContextTypes

from telegram_smart_bots.bots.voice_journal.services.text import add_text
from telegram_smart_bots.shared.utils import async_typing

logger = logging.getLogger(__name__)


@async_typing
async def modify_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = mongodb_manager.get_database(os.getenv("DB_NAME"))
    collection = db["journals"]
    reply_msg = "😿"
    try:
        msg_date = int(update.message.reply_to_message.text.split(":=")[0].strip())
        new_text = update.message.text.split(":=")[-1].strip()
        await collection.update_one(
            {"telegram_id": update.message.from_user.id},
            {
                "$set": {
                    f"journal.{date.fromtimestamp(msg_date)}.messages.{msg_date}": new_text
                }
            },
            upsert=True,
        )
        reply_msg = f"{msg_date}:={new_text}"
    except Exception as ex:
        logger.error(ex)
        reply_msg = "😿"
    finally:
        context.user_data[update.update_id] = "Done"
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=reply_msg,
            reply_to_message_id=update.message.id,
        )


@async_typing
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_date = update.message.date
    forward_date = update.message.forward_date
    user_id = update.message.from_user.id
    msg_date = message_date if forward_date is None else forward_date
    msg_date = int(msg_date.timestamp())
    text = update.message.text

    reply_msg = await add_text(user_id, msg_date, text)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=reply_msg,
        reply_to_message_id=update.message.id,
    )
