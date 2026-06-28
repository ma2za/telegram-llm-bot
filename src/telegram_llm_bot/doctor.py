import argparse
import asyncio
import os

from telegram_llm_bot.config import load_bot_config
from telegram_llm_bot.paths import load_environment
from telegram_llm_bot.paths import environment_files
from telegram_llm_bot.shared.chat import (
    OLLAMA_DEFAULT_MODEL,
    ollama_base_url,
    ollama_model,
    ollama_options,
)
from telegram_llm_bot.shared.db.mongo import mongodb_manager
from telegram_llm_bot.shared.readiness import (
    FAIL,
    OK,
    ReadinessResult,
    check_minio_readiness,
    check_ollama_readiness,
    check_sqlite_readiness,
    check_telegram_readiness,
)

load_environment()


def check_environment_files(results: list[ReadinessResult]) -> None:
    detected = [str(path) for path in environment_files() if path.exists()]
    if detected:
        results.append(ReadinessResult(OK, f"Env files: {', '.join(detected)}"))
    else:
        results.append(ReadinessResult(OK, "Env files: none"))


def check_bot_config(results: list[ReadinessResult]) -> None:
    config = load_bot_config()
    results.append(ReadinessResult(OK, f"Bot config: {config.path}"))


def check_provider_config(results: list[ReadinessResult]) -> str:
    provider = os.getenv("LLM_PROVIDER", "").strip().lower()
    if provider not in {"ollama", "beam", "echo"}:
        raise ValueError("Set LLM_PROVIDER to ollama, beam, or echo")

    if provider == "ollama":
        ollama_base_url()
        model = ollama_model() or OLLAMA_DEFAULT_MODEL
        ollama_options()
        results.append(ReadinessResult(OK, f"Ollama configured: {model}"))
    elif provider == "beam":
        if not os.getenv("BEAM_URL") or not os.getenv("BEAM_TOKEN"):
            raise ValueError("Set BEAM_URL and BEAM_TOKEN when LLM_PROVIDER=beam")
        results.append(ReadinessResult(OK, "Beam configured"))
    else:
        results.append(ReadinessResult(OK, "Echo provider configured"))
    return provider


def check_history_config(results: list[ReadinessResult]) -> str:
    backend = os.getenv("CHAT_HISTORY_BACKEND", "sqlite").strip().lower()
    if backend not in {"sqlite", "memory", "mongo"}:
        raise ValueError("Set CHAT_HISTORY_BACKEND to sqlite, memory, or mongo")

    if backend == "sqlite":
        results.append(check_sqlite_readiness())
    elif backend == "mongo":
        if not os.getenv("MONGO_HOST") or not os.getenv("MONGO_PORT"):
            raise ValueError("Set MONGO_HOST and MONGO_PORT when CHAT_HISTORY_BACKEND=mongo")
        results.append(ReadinessResult(OK, "Mongo configured"))
    else:
        results.append(ReadinessResult(OK, "Memory history configured"))
    return backend


async def check_live(provider: str, backend: str, results: list[ReadinessResult]) -> None:
    results.append(check_telegram_readiness())
    if provider == "ollama":
        results.append(await check_ollama_readiness())
    results.append(await check_minio_readiness())
    if backend == "mongo":
        await mongodb_manager.ping()
        results.append(ReadinessResult(OK, "Mongo live ping ok"))


async def doctor_async(live: bool = False) -> int:
    results = []
    try:
        check_environment_files(results)
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token or token == "replace-me":
            raise ValueError("Set TELEGRAM_BOT_TOKEN in the bot .env file")
        results.append(ReadinessResult(OK, "Telegram token present"))

        settings_module = os.getenv("SETTINGS_FILE", "telegram_llm_bot.bots.base_chatbot.settings")
        results.append(ReadinessResult(OK, f"Settings module: {settings_module}"))
        check_bot_config(results)

        if not os.getenv("BOT_NAME"):
            raise ValueError("Set BOT_NAME in the bot .env file")
        results.append(ReadinessResult(OK, f"Bot name: {os.getenv('BOT_NAME')}"))

        provider = check_provider_config(results)
        backend = check_history_config(results)
        if live:
            await check_live(provider, backend, results)
    except Exception as ex:
        results.append(ReadinessResult(FAIL, str(ex)))

    for result in results:
        print(f"{result.severity}: {result.message}")
    return 1 if any(result.failed for result in results) else 0


def doctor() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(doctor_async(args.live)))


if __name__ == "__main__":
    doctor()
