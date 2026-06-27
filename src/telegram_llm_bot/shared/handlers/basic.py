import importlib
import logging
import os

from telegram import Update
from telegram.ext import ContextTypes

from telegram_llm_bot.config import bot_config_path
from telegram_llm_bot.shared.chat import OLLAMA_DEFAULT_MODEL, ollama_options
from telegram_llm_bot.shared.history.history import get_chat_history
from telegram_llm_bot.shared.services.basic import set_language
from telegram_llm_bot.shared.utils import async_typing

settings = importlib.import_module(os.getenv("SETTINGS_FILE"))

logger = logging.getLogger(__name__)


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


def help_text() -> str:
    return "\n".join(
        [
            "/help - show bot commands",
            "/model - show provider, model, and history backend",
            "/settings - show active non-secret settings",
            "/reset - clear your chat history",
            "/my_id - show your Telegram user id",
        ]
    )


def settings_text() -> str:
    return "\n".join(
        [
            f"Bot: {os.getenv('BOT_NAME', 'unknown')}",
            f"Config: {bot_config_path()}",
            model_status_text(),
        ]
    )


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
    chat_history = get_chat_history(os.getenv("BOT_NAME"), update.message.from_user.id)
    await chat_history.clear()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Chat history reset.",
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
        text=settings_text(),
        reply_to_message_id=update.message.id,
    )
