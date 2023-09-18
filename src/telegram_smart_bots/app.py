# TODO I don't like the path
# TODO I don't like it before the imports
import logging.config

from dotenv import load_dotenv

from telegram_smart_bots.shared.db.mongo import mongodb_manager

load_dotenv()

logging.config.fileConfig("../../logging.conf", disable_existing_loggers=False)

logger = logging.getLogger(__name__)

import os
from pathlib import Path

from telegram import Update
from telegram.ext import Application, CommandHandler

from telegram_smart_bots.shared.handlers.basic import (
    handle_start,
    handle_telegram_id,
    handle_language,
)


async def post_init(application: Application) -> None:
    await application.bot.set_my_commands(
        [("my_id", "my_id"), ("language", "language lang")]
    )


def main() -> None:
    Path(".tmp").mkdir(parents=True, exist_ok=True)

    app = (
        Application.builder()
        .token(os.getenv("TELEGRAM_BOT_TOKEN"))
        .post_init(post_init)
        .build()
    )

    app.add_handlers(
        [
            CommandHandler("start", handle_start, block=False),
            CommandHandler("my_id", handle_telegram_id, block=False),
            CommandHandler("language", handle_language, block=False),
        ]
    )
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    try:
        main()
    except Exception as ex:
        logger.error(ex)
    finally:
        mongodb_manager.close()
