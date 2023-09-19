import logging
import os
from datetime import date

from langchain.schema import HumanMessage
from telegram import Update
from telegram.ext import ContextTypes

from telegram_smart_bots.shared.history.history import MongoDBChatMessageHistory
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


async def add_text(user_id: int, msg_date: int, text: str):
    try:
        chat_history = MongoDBChatMessageHistory(
            os.getenv("DB_NAME"), user_id, f"{date.fromtimestamp(msg_date)}", "messages"
        )
        response = HumanMessage(content=text)
        response.additional_kwargs["timestamp"] = msg_date
        await chat_history.add_message(response)

        reply_msg = f"{msg_date}:={text}"
    except Exception as ex:
        logger.error(ex)
        reply_msg = "😿"
    return reply_msg
