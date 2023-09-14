import asyncio
import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, filters
from telegram.ext import ContextTypes

load_dotenv()

from handlers.message import handle_message
from telegram_llm_guru.db import mongodb_manager
from telegram_llm_guru.utils import typing_loop

# TODO logging

# logging.basicConfig(
#     filename="logs/bot.log",
#     level=logging.DEBUG,
#     format="%(asctime)s %(levelname)s %(name)s %(message)s",
# )
logger = logging.getLogger(__name__)


def async_partial(op):
    async def inner(update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data[update.update_id] = None
        await asyncio.gather(typing_loop(update, context), op(update, context))
        del context.user_data[update.update_id]

    return inner


def main() -> None:
    app = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()

    app.add_handlers(
        [MessageHandler(filters.TEXT, async_partial(handle_message), block=False)]
    )
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    try:
        main()
    finally:
        mongodb_manager.close()
