import asyncio
import hashlib
import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from async_lru import alru_cache
from faster_whisper import WhisperModel

from telegram_llm_bot.paths import PROJECT_DIR


def transcription_model() -> str:
    return os.getenv("LOCAL_TRANSCRIPTION_MODEL", "small")


def transcription_compute_type() -> str:
    return os.getenv("LOCAL_TRANSCRIPTION_COMPUTE_TYPE", "int8")


def transcription_device() -> str:
    return os.getenv("LOCAL_TRANSCRIPTION_DEVICE", "cpu")


def transcription_beam_size() -> int:
    return int(os.getenv("LOCAL_TRANSCRIPTION_BEAM_SIZE", "5"))


def transcription_cpu_threads() -> int:
    return int(os.getenv("LOCAL_TRANSCRIPTION_CPU_THREADS", "4"))


def temp_audio_path(voice: bytes) -> Path:
    return PROJECT_DIR / ".tmp" / f"{hashlib.sha256(voice).hexdigest()}.oga"


@lru_cache
def local_transcription_model() -> WhisperModel:
    return WhisperModel(
        transcription_model(),
        device=transcription_device(),
        compute_type=transcription_compute_type(),
        cpu_threads=transcription_cpu_threads(),
    )


def transcribe_file(path: Path, language: Optional[str] = None) -> str:
    kwargs = {"beam_size": transcription_beam_size(), "vad_filter": True}
    if language:
        kwargs["language"] = language
    segments, _ = local_transcription_model().transcribe(str(path), **kwargs)
    return " ".join(segment.text.strip() for segment in segments).strip()


@alru_cache
async def transcribe(
    voice: bytes,
    user_id: int = None,
    duration: int = None,
    language: Optional[str] = None,
) -> str:
    path = temp_audio_path(voice)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(voice)
    try:
        return await asyncio.to_thread(transcribe_file, path, language)
    finally:
        path.unlink(missing_ok=True)
