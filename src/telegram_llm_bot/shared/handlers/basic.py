import importlib
import logging
import os

from telegram import Update
from telegram.ext import ContextTypes

from telegram_llm_bot.config import bot_config_path
from telegram_llm_bot.shared.chat import OLLAMA_DEFAULT_MODEL, ollama_options
from telegram_llm_bot.shared.history.history import (
    DEFAULT_SESSION_ID,
    clear_user_sessions,
    delete_session,
    get_active_session,
    get_chat_history,
    list_sessions,
    set_active_session,
)
from telegram_llm_bot.shared.readiness import (
    check_minio_readiness,
    check_ollama_readiness,
    check_sqlite_readiness,
)
from telegram_llm_bot.shared.services.basic import set_language
from telegram_llm_bot.shared.utils import async_typing

settings = importlib.import_module(
    os.getenv("SETTINGS_FILE", "telegram_llm_bot.bots.base_chatbot.settings")
)

logger = logging.getLogger(__name__)


def bot_name() -> str:
    return os.getenv("BOT_NAME")


def session_name(args) -> str:
    if len(args) != 1:
        raise ValueError("Provide one session name.")
    name = args[0].strip()
    if not name:
        raise ValueError("Session name cannot be empty.")
    if len(name) > 64:
        raise ValueError("Session name must be 64 characters or fewer.")
    return name


def model_status_text() -> str:
    provider = os.getenv("LLM_PROVIDER", "unknown").strip().lower()
    backend = os.getenv("CHAT_HISTORY_BACKEND", "sqlite").strip().lower()
    context = None
    if provider == "ollama":
        model = os.getenv("OLLAMA_MODEL", OLLAMA_DEFAULT_MODEL)
        context = str(ollama_options()["num_ctx"])
    elif provider == "beam":
        model = os.getenv("BEAM_APP_NAME", "beam")
    elif provider == "echo":
        model = "echo"
    else:
        model = "unknown"
    lines = [f"Provider: {provider}", f"Model: {model}", f"History: {backend}"]
    if context:
        lines.append(f"Context: {context}")
    return "\n".join(lines)


async def health_text(user_id: int = None) -> str:
    lines = [
        "Status: ok",
        f"Bot: {os.getenv('BOT_NAME', 'unknown')}",
        model_status_text(),
    ]
    if user_id is not None:
        lines.append(f"Session: {await get_active_session(bot_name(), user_id)}")
    if os.getenv("CHAT_HISTORY_BACKEND", "sqlite").strip().lower() == "sqlite":
        sqlite = check_sqlite_readiness()
        lines.append(f"{sqlite.severity}: {sqlite.message}")
    ollama = await check_ollama_readiness()
    minio = await check_minio_readiness()
    lines.append(f"{ollama.severity}: {ollama.message}")
    lines.append(f"{minio.severity}: {minio.message}")
    return "\n".join(lines)


def help_text() -> str:
    return "\n".join(
        [
            "/help - show bot commands",
            "/health - show runtime health",
            "/model - show provider, model, and history backend",
            "/settings - show active non-secret settings",
            "/reset - clear your chat history",
            "/session - show current session",
            "/new <name> - create or switch to a session",
            "/sessions - list your sessions",
            "/use <name> - switch to an existing session",
            "/delete <name> - delete a session",
            "/reset_all - clear all your sessions",
            "/my_id - show your Telegram user id",
        ]
    )


async def settings_text(user_id: int = None) -> str:
    lines = [
        f"Bot: {os.getenv('BOT_NAME', 'unknown')}",
        f"Config: {bot_config_path()}",
    ]
    if user_id is not None:
        lines.append(f"Session: {await get_active_session(bot_name(), user_id)}")
    lines.append(model_status_text())
    return "\n".join(lines)


async def session_text(user_id: int) -> str:
    return f"Current session: {await get_active_session(bot_name(), user_id)}"


async def new_session_text(user_id: int, args) -> str:
    try:
        name = session_name(args)
    except ValueError as ex:
        return str(ex)
    await set_active_session(bot_name(), user_id, name)
    return f"Current session: {name}"


async def sessions_text(user_id: int) -> str:
    sessions = await list_sessions(bot_name(), user_id)
    active = await get_active_session(bot_name(), user_id)
    return "\n".join(
        [f"Sessions ({len(sessions)}):"]
        + [f"{'*' if session == active else '-'} {session}" for session in sessions]
    )


async def use_session_text(user_id: int, args) -> str:
    try:
        name = session_name(args)
    except ValueError as ex:
        return str(ex)
    sessions = await list_sessions(bot_name(), user_id)
    if name not in sessions:
        return f"Session not found: {name}"
    await set_active_session(bot_name(), user_id, name)
    return f"Current session: {name}"


async def delete_session_text(user_id: int, args) -> str:
    try:
        name = session_name(args)
    except ValueError as ex:
        return str(ex)
    if name == DEFAULT_SESSION_ID:
        return "The default session cannot be deleted."
    deleted = await delete_session(bot_name(), user_id, name)
    return f"Deleted session: {name}" if deleted else f"Session not found: {name}"


@async_typing
async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=settings.settings.start_message,
        reply_to_message_id=update.message.id,
    )


@async_typing
async def handle_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=update.message.from_user.id,
        reply_to_message_id=update.message.id,
    )


@async_typing
async def handle_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # TODO replace with pydantic
    if len(context.args) != 1:
        reply_msg = "😿"
    else:
        reply_msg = await set_language(update.message.from_user.id, context.args[0])
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=reply_msg,
        reply_to_message_id=update.message.id,
    )


@async_typing
async def handle_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session_id = await get_active_session(bot_name(), update.message.from_user.id)
    chat_history = get_chat_history(bot_name(), update.message.from_user.id, session_id)
    await chat_history.clear()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Chat history reset for session: {session_id}",
        reply_to_message_id=update.message.id,
    )


@async_typing
async def handle_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=model_status_text(),
        reply_to_message_id=update.message.id,
    )


@async_typing
async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=help_text(),
        reply_to_message_id=update.message.id,
    )


@async_typing
async def handle_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=await settings_text(update.message.from_user.id),
        reply_to_message_id=update.message.id,
    )


@async_typing
async def handle_health(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=await health_text(update.message.from_user.id),
        reply_to_message_id=update.message.id,
    )


@async_typing
async def handle_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=await session_text(update.message.from_user.id),
        reply_to_message_id=update.message.id,
    )


@async_typing
async def handle_new_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=await new_session_text(update.message.from_user.id, context.args),
        reply_to_message_id=update.message.id,
    )


@async_typing
async def handle_sessions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=await sessions_text(update.message.from_user.id),
        reply_to_message_id=update.message.id,
    )


@async_typing
async def handle_use_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=await use_session_text(update.message.from_user.id, context.args),
        reply_to_message_id=update.message.id,
    )


@async_typing
async def handle_delete_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=await delete_session_text(update.message.from_user.id, context.args),
        reply_to_message_id=update.message.id,
    )


@async_typing
async def handle_reset_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await clear_user_sessions(bot_name(), update.message.from_user.id)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="All chat sessions reset.",
        reply_to_message_id=update.message.id,
    )
