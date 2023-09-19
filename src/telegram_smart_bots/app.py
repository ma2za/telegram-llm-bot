# TODO I don't like the path
# TODO I don't like it before the imports
import importlib
import logging.config
import os

from dotenv import load_dotenv

load_dotenv("./bots/voice_journal/.env")

settings = importlib.import_module(os.getenv("SETTINGS_FILE"))

logging.config.fileConfig("../../logging.conf", disable_existing_loggers=False)

logger = logging.getLogger(__name__)

from pathlib import Path

from telegram import Update
from telegram.ext import Application, CommandHandler

from telegram_smart_bots.shared.db.mongo import mongodb_manager
from telegram_smart_bots.shared.handlers.basic import (
    handle_start,
    handle_user_id,
    handle_language,
)


async def post_init(application: Application) -> None:
    await application.bot.set_my_commands(
        [("my_id", "my_id"), ("language", "language lang")]
        + list(settings.settings.commands.items())
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
            CommandHandler("my_id", handle_user_id, block=False),
            CommandHandler("language", handle_language, block=False),
        ]
        + settings.settings.handlers
    )
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    try:
        main()
    except Exception as ex:
        logger.error(ex)
    finally:
        mongodb_manager.close()
