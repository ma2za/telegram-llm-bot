import importlib
import logging.config
import os
import sys
from pathlib import Path

from langchain.schema import HumanMessage, SystemMessage
from telegram import Update
from telegram.ext import Application, CommandHandler

from telegram_llm_bot.paths import LOGGING_CONFIG, LOG_DIR, PACKAGE_DIR, load_environment

load_environment()
settings_module = os.getenv(
    "SETTINGS_FILE", "telegram_llm_bot.bots.base_chatbot.settings"
)
settings = importlib.import_module(settings_module)

LOG_DIR.mkdir(parents=True, exist_ok=True)
os.chdir(PACKAGE_DIR)
logging.config.fileConfig(LOGGING_CONFIG, disable_existing_loggers=False)

logger = logging.getLogger(__name__)

from telegram_llm_bot.shared.db.mongo import mongodb_manager
from telegram_llm_bot.shared.handlers.basic import (
    handle_start,
    handle_user_id,
    handle_language,
    handle_reset,
    handle_model,
)
from telegram_llm_bot.shared.chat import chat
from telegram_llm_bot.shared.chat import ollama_base_url, ollama_model, ollama_options


def build_application() -> Application:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token or token == "replace-me":
        raise ValueError(
            "Set TELEGRAM_BOT_TOKEN in src/telegram_llm_bot/bots/base_chatbot/.env"
        )

    app = Application.builder().token(token).post_init(post_init).build()
    app.add_handlers(
        [
            CommandHandler("start", handle_start, block=False),
            CommandHandler("my_id", handle_user_id, block=False),
            CommandHandler("language", handle_language, block=False),
            CommandHandler("reset", handle_reset, block=False),
            CommandHandler("model", handle_model, block=False),
        ]
        + settings.settings.handlers
    )
    return app


async def post_init(application: Application) -> None:
    await application.bot.set_my_commands(
        [
            ("my_id", "show your Telegram user id"),
            ("language", "language lang"),
            ("reset", "clear your chat history"),
            ("model", "show active provider and history backend"),
        ]
        + list(settings.settings.commands.items())
    )


def smoke() -> None:
    Path(".tmp").mkdir(parents=True, exist_ok=True)
    if not os.getenv("SETTINGS_FILE"):
        raise ValueError("Set SETTINGS_FILE in src/telegram_llm_bot/bots/base_chatbot/.env")
    if not os.getenv("BOT_NAME"):
        raise ValueError("Set BOT_NAME in src/telegram_llm_bot/bots/base_chatbot/.env")
    backend = os.getenv("CHAT_HISTORY_BACKEND", "sqlite").strip().lower()
    if backend == "mongo" and (not os.getenv("MONGO_HOST") or not os.getenv("MONGO_PORT")):
        raise ValueError("Set MONGO_HOST and MONGO_PORT in .env when CHAT_HISTORY_BACKEND=mongo")
    provider = os.getenv("LLM_PROVIDER")
    if not provider:
        raise ValueError("Set LLM_PROVIDER in .env")
    if provider.strip().lower() == "ollama":
        ollama_base_url()
        ollama_model()
        ollama_options()
    print(f"Loaded bot: {os.getenv('BOT_NAME')}")
    print(f"Loaded handlers: {len(settings.settings.handlers) + 5}")
    print(f"Loaded provider: {provider}")
    print(f"Loaded history: {backend}")
    print("Smoke run ok")


async def check_provider() -> None:
    response = await chat(
        [
            SystemMessage(content="Reply with exactly: ok"),
            HumanMessage(content="Say ok"),
        ]
    )
    print(response)


def provider_check() -> None:
    import asyncio

    asyncio.run(check_provider())


def main() -> None:
    Path(".tmp").mkdir(parents=True, exist_ok=True)
    app = build_application()
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    try:
        if "--smoke" in sys.argv:
            smoke()
        elif "--provider-check" in sys.argv:
            provider_check()
        else:
            main()
    except Exception as ex:
        logger.exception(ex)
        raise
    finally:
        if "mongodb_manager" in globals():
            mongodb_manager.close()
