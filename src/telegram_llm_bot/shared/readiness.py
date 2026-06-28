import os
import socket
import tempfile
from dataclasses import dataclass
from pathlib import Path

import httpx
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError, EndpointConnectionError

from telegram_llm_bot.paths import PROJECT_DIR
from telegram_llm_bot.shared.chat import ollama_base_url, ollama_model
from telegram_llm_bot.shared.db.minio_storage import minio_storage

OK = "OK"
WARN = "WARN"
FAIL = "FAIL"


@dataclass
class ReadinessResult:
    severity: str
    message: str

    @property
    def failed(self) -> bool:
        return self.severity == FAIL


def sqlite_path() -> Path:
    configured = os.getenv("SQLITE_HISTORY_PATH", ".tmp/chat_history.sqlite3")
    path = Path(configured)
    return path if path.is_absolute() else PROJECT_DIR / path


def check_sqlite_readiness() -> ReadinessResult:
    path = sqlite_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=True):
            pass
    except OSError:
        return ReadinessResult(FAIL, "SQLite path writable: no")
    return ReadinessResult(OK, "SQLite path writable: yes")


def telegram_http_get(url: str, timeout: float, follow_redirects: bool):
    transport = httpx.HTTPTransport(trust_env=False, local_address="0.0.0.0")
    with httpx.Client(transport=transport, timeout=timeout, trust_env=False) as client:
        return client.get(url, follow_redirects=follow_redirects)


def check_telegram_readiness(
    resolve=socket.getaddrinfo, http_get=telegram_http_get
) -> ReadinessResult:
    try:
        resolve("api.telegram.org", 443, type=socket.SOCK_STREAM)
    except OSError:
        return ReadinessResult(FAIL, "Telegram DNS: unavailable")

    try:
        response = http_get("https://api.telegram.org", timeout=10.0, follow_redirects=False)
    except httpx.HTTPError:
        return ReadinessResult(FAIL, "Telegram HTTPS: unavailable")

    return ReadinessResult(OK, f"Telegram HTTPS: reachable ({response.status_code})")


async def check_ollama_readiness() -> ReadinessResult:
    provider = os.getenv("LLM_PROVIDER", "").strip().lower()
    if provider != "ollama":
        return ReadinessResult(OK, "Ollama: not selected")

    base_url = ollama_base_url()
    try:
        async with httpx.AsyncClient(trust_env=False) as client:
            response = await client.get(
                f"{base_url}/api/tags",
                timeout=float(os.getenv("OLLAMA_HEALTH_TIMEOUT", "5")),
            )
        response.raise_for_status()
    except httpx.HTTPError:
        return ReadinessResult(WARN, f"Ollama: unreachable for model {ollama_model()}")
    return ReadinessResult(OK, f"Ollama: reachable for model {ollama_model()}")


async def check_minio_readiness(storage=minio_storage) -> ReadinessResult:
    try:
        bucket = storage.bucket_name()
        kwargs = storage.client_kwargs()
        timeout = float(os.getenv("MINIO_HEALTH_TIMEOUT", "5"))
        kwargs["config"] = Config(connect_timeout=timeout, read_timeout=timeout)
        async with storage.session.client(**kwargs) as client:
            await client.list_buckets()
    except RuntimeError as ex:
        return ReadinessResult(FAIL, f"MinIO: {ex}")
    except EndpointConnectionError:
        return ReadinessResult(WARN, f"MinIO: unreachable for bucket {bucket}")
    except (BotoCoreError, ClientError):
        return ReadinessResult(WARN, f"MinIO: unavailable for bucket {bucket}")
    return ReadinessResult(OK, f"MinIO: reachable for bucket {bucket}")
