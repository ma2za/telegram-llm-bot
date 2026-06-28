import hashlib
import logging
import os
from datetime import datetime
from urllib.parse import urlsplit, urlunsplit

from telegram_llm_bot.bots.base_chatbot.services.text import text_chat_service, user_error_message
from telegram_llm_bot.shared.audio import transcribe
from telegram_llm_bot.shared.db.minio_storage import minio_storage
from telegram_llm_bot.shared.history.history import get_active_session

logger = logging.getLogger(__name__)


def voice_object_name(user_id: int, session_id: str, audio: bytes) -> str:
    digest = hashlib.sha256(audio).hexdigest()
    return f"voice/{user_id}/{session_id}/{digest}.oga"


def sanitized_endpoint(endpoint_url: str = None) -> str:
    endpoint_url = endpoint_url or os.getenv("MINIO_ENDPOINT_URL", "")
    if not endpoint_url:
        return "not configured"
    parts = urlsplit(endpoint_url)
    host = parts.hostname or ""
    if parts.port:
        host = f"{host}:{parts.port}"
    return urlunsplit((parts.scheme, host, "", "", ""))


async def archive_voice_audio(object_name: str, audio: bytes) -> None:
    try:
        await minio_storage.put_object(object_name, audio, content_type="audio/ogg")
    except Exception as ex:
        logger.warning(
            "Voice archive storage failed: endpoint=%s bucket=%s object=%s error=%s",
            sanitized_endpoint(),
            os.getenv("MINIO_BUCKET") or os.getenv("BOT_NAME") or "not configured",
            object_name,
            ex,
        )


async def voice_chat_service(
    audio: bytes,
    user_id: int,
    duration: int,
    msg_date: datetime,
) -> str:
    try:
        bot_name = os.getenv("BOT_NAME")
        session_id = await get_active_session(bot_name, user_id)
        object_name = voice_object_name(user_id, session_id, audio)
        await archive_voice_audio(object_name, audio)
        transcript = await transcribe(audio, user_id=user_id, duration=duration)
        if not transcript:
            return "I could not transcribe that voice message."
        return await text_chat_service(user_id, transcript, msg_date)
    except Exception as ex:
        logger.exception(ex)
        return user_error_message(ex)


new_note = voice_chat_service
