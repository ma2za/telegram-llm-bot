import argparse
import asyncio
import os
import tempfile
from pathlib import Path

from telegram_llm_bot.config import load_bot_config
from telegram_llm_bot.paths import PROJECT_DIR, load_environment
from telegram_llm_bot.paths import environment_files
from telegram_llm_bot.shared.chat import (
    OLLAMA_DEFAULT_MODEL,
    chat,
    ollama_base_url,
    ollama_model,
    ollama_options,
)
from telegram_llm_bot.shared.db.mongo import mongodb_manager
from telegram_llm_bot.shared.messages import HumanMessage, SystemMessage

load_environment()


def sqlite_path() -> Path:
    configured = os.getenv("SQLITE_HISTORY_PATH", ".tmp/chat_history.sqlite3")
    path = Path(configured)
    return path if path.is_absolute() else PROJECT_DIR / path


def check_sqlite_path(results: list[tuple[bool, str]]) -> None:
    path = sqlite_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=True):
        pass
    results.append((True, f"SQLite path writable: {path}"))


def check_environment_files(results: list[tuple[bool, str]]) -> None:
    detected = [str(path) for path in environment_files() if path.exists()]
    if detected:
        results.append((True, f"Env files: {', '.join(detected)}"))
    else:
        results.append((True, "Env files: none"))


def check_bot_config(results: list[tuple[bool, str]]) -> None:
    config = load_bot_config()
    results.append((True, f"Bot config: {config.path}"))


def check_provider_config(results: list[tuple[bool, str]]) -> str:
    provider = os.getenv("LLM_PROVIDER", "").strip().lower()
    if provider not in {"ollama", "beam", "echo"}:
        raise ValueError("Set LLM_PROVIDER to ollama, beam, or echo")

    if provider == "ollama":
        ollama_base_url()
        model = ollama_model() or OLLAMA_DEFAULT_MODEL
        ollama_options()
        results.append((True, f"Ollama configured: {model}"))
    elif provider == "beam":
        if not os.getenv("BEAM_URL") or not os.getenv("BEAM_TOKEN"):
            raise ValueError("Set BEAM_URL and BEAM_TOKEN when LLM_PROVIDER=beam")
        results.append((True, "Beam configured"))
    else:
        results.append((True, "Echo provider configured"))
    return provider


def check_history_config(results: list[tuple[bool, str]]) -> str:
    backend = os.getenv("CHAT_HISTORY_BACKEND", "sqlite").strip().lower()
    if backend not in {"sqlite", "memory", "mongo"}:
        raise ValueError("Set CHAT_HISTORY_BACKEND to sqlite, memory, or mongo")

    if backend == "sqlite":
        check_sqlite_path(results)
    elif backend == "mongo":
        if not os.getenv("MONGO_HOST") or not os.getenv("MONGO_PORT"):
            raise ValueError("Set MONGO_HOST and MONGO_PORT when CHAT_HISTORY_BACKEND=mongo")
        results.append((True, "Mongo configured"))
    else:
        results.append((True, "Memory history configured"))
    return backend


async def check_live(provider: str, backend: str, results: list[tuple[bool, str]]) -> None:
    if provider == "ollama":
        response = await chat(
            [
                SystemMessage(content="Reply with exactly: ok"),
                HumanMessage(content="Say ok"),
            ]
        )
        results.append((True, f"Ollama live response: {response}"))
    if backend == "mongo":
        await mongodb_manager.ping()
        results.append((True, "Mongo live ping ok"))


async def doctor_async(live: bool = False) -> int:
    results = []
    try:
        check_environment_files(results)
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token or token == "replace-me":
            raise ValueError("Set TELEGRAM_BOT_TOKEN in the bot .env file")
        results.append((True, "Telegram token present"))

        settings_module = os.getenv("SETTINGS_FILE", "telegram_llm_bot.bots.base_chatbot.settings")
        results.append((True, f"Settings module: {settings_module}"))
        check_bot_config(results)

        if not os.getenv("BOT_NAME"):
            raise ValueError("Set BOT_NAME in the bot .env file")
        results.append((True, f"Bot name: {os.getenv('BOT_NAME')}"))

        provider = check_provider_config(results)
        backend = check_history_config(results)
        if live:
            await check_live(provider, backend, results)
    except Exception as ex:
        results.append((False, str(ex)))

    for ok, message in results:
        status = "OK" if ok else "FAIL"
        print(f"{status}: {message}")
    return 0 if all(ok for ok, _ in results) else 1


def doctor() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    raise SystemExit(asyncio.run(doctor_async(args.live)))


if __name__ == "__main__":
    doctor()
