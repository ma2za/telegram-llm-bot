import importlib
import logging.config
import os
import socket
import sys
from pathlib import Path

import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler
from telegram.request import HTTPXRequest

from telegram_llm_bot.paths import LOGGING_CONFIG, LOG_DIR, PACKAGE_DIR, load_environment

load_environment()
settings_module = os.getenv("SETTINGS_FILE", "telegram_llm_bot.bots.base_chatbot.settings")
settings = importlib.import_module(settings_module)

LOG_DIR.mkdir(parents=True, exist_ok=True)
os.chdir(PACKAGE_DIR)
logging.config.fileConfig(LOGGING_CONFIG, disable_existing_loggers=False)

logger = logging.getLogger(__name__)
TELEGRAM_API_HOST = "api.telegram.org"
TELEGRAM_API_URL = f"https://{TELEGRAM_API_HOST}"

from telegram_llm_bot.shared.db.mongo import mongodb_manager
from telegram_llm_bot.shared.messages import HumanMessage, SystemMessage
from telegram_llm_bot.shared.handlers.basic import (
    handle_start,
    handle_user_id,
    handle_language,
    handle_reset,
    handle_model,
    handle_help,
    handle_health,
    handle_settings,
    handle_session,
    handle_new_session,
    handle_sessions,
    handle_use_session,
    handle_delete_session,
    handle_reset_all,
)
from telegram_llm_bot.shared.chat import chat
from telegram_llm_bot.shared.chat import ollama_base_url, ollama_model, ollama_options


def runtime_model_name(provider: str) -> str:
    if provider == "ollama":
        return ollama_model()
    if provider == "beam":
        return os.getenv("BEAM_APP_NAME", "beam")
    if provider == "echo":
        return "echo"
    return "unknown"


def log_startup_config() -> None:
    provider = os.getenv("LLM_PROVIDER", "unknown").strip().lower()
    logger.info("Bot name: %s", os.getenv("BOT_NAME", "unknown"))
    logger.info("Provider: %s", provider)
    logger.info("Model: %s", runtime_model_name(provider))
    logger.info("History backend: %s", os.getenv("CHAT_HISTORY_BACKEND", "sqlite"))
    logger.info("Bot config: %s", settings.settings.config_file)


def telegram_http_get(url: str, timeout: float, follow_redirects: bool):
    transport = httpx.HTTPTransport(trust_env=False, local_address="0.0.0.0")
    with httpx.Client(transport=transport, timeout=timeout, trust_env=False) as client:
        return client.get(url, follow_redirects=follow_redirects)


def telegram_httpx_kwargs(connection_pool_size: int) -> dict:
    return {
        "trust_env": False,
        "transport": httpx.AsyncHTTPTransport(
            trust_env=False,
            local_address="0.0.0.0",
            limits=httpx.Limits(
                max_connections=connection_pool_size,
                max_keepalive_connections=connection_pool_size,
            ),
        ),
    }


def check_telegram_api_reachable(resolve=socket.getaddrinfo, http_get=telegram_http_get) -> None:
    try:
        resolve(TELEGRAM_API_HOST, 443, type=socket.SOCK_STREAM)
    except OSError as ex:
        raise RuntimeError(
            "Cannot resolve api.telegram.org. Check DNS, VPN, proxy, or network settings."
        ) from ex

    try:
        response = http_get(TELEGRAM_API_URL, timeout=10.0, follow_redirects=False)
    except httpx.HTTPError as ex:
        raise RuntimeError(
            "Cannot reach api.telegram.org over HTTPS. Check VPN, proxy, firewall, or network settings."
        ) from ex

    logger.info("Telegram API preflight ok: HTTPS status %s", response.status_code)


def build_application() -> Application:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token or token == "replace-me":
        raise ValueError("Set TELEGRAM_BOT_TOKEN in src/telegram_llm_bot/bots/base_chatbot/.env")

    request = HTTPXRequest(connection_pool_size=256, httpx_kwargs=telegram_httpx_kwargs(256))
    get_updates_request = HTTPXRequest(httpx_kwargs=telegram_httpx_kwargs(1))
    app = (
        Application.builder()
        .token(token)
        .request(request)
        .get_updates_request(get_updates_request)
        .post_init(post_init)
        .build()
    )
    app.add_handlers(
        [
            CommandHandler("start", handle_start, block=False),
            CommandHandler("my_id", handle_user_id, block=False),
            CommandHandler("language", handle_language, block=False),
            CommandHandler("reset", handle_reset, block=False),
            CommandHandler("model", handle_model, block=False),
            CommandHandler("help", handle_help, block=False),
            CommandHandler("health", handle_health, block=False),
            CommandHandler("settings", handle_settings, block=False),
            CommandHandler("session", handle_session, block=False),
            CommandHandler("new", handle_new_session, block=False),
            CommandHandler("sessions", handle_sessions, block=False),
            CommandHandler("use", handle_use_session, block=False),
            CommandHandler("delete", handle_delete_session, block=False),
            CommandHandler("reset_all", handle_reset_all, block=False),
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
            ("help", "show bot commands"),
            ("health", "show runtime health"),
            ("settings", "show active non-secret settings"),
            ("session", "show current session"),
            ("new", "new session name"),
            ("sessions", "list sessions"),
            ("use", "use session name"),
            ("delete", "delete session name"),
            ("reset_all", "clear all your sessions"),
        ]
        + list(settings.settings.commands.items())
    )


def smoke() -> None:
    Path(".tmp").mkdir(parents=True, exist_ok=True)
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
    print(f"Loaded handlers: {len(settings.settings.handlers) + 14}")
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
    log_startup_config()
    check_telegram_api_reachable()
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
