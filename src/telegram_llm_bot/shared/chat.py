import logging
import os
from typing import List

import httpx

from telegram_llm_bot.shared.messages import BaseMessage

logger = logging.getLogger(__name__)

OLLAMA_DEFAULT_MODEL = "qwen2.5:0.5b"


def get_chat_provider():
    provider = os.getenv("LLM_PROVIDER")
    if not provider:
        raise ValueError("Set LLM_PROVIDER to ollama, beam, or echo")
    provider = provider.strip().lower()
    if provider == "ollama":
        return ollama_chat
    if provider == "beam":
        return beam_chat_messages
    if provider == "echo":
        return echo_chat
    raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")


async def chat(messages: List[BaseMessage]) -> str:
    provider = get_chat_provider()
    return await provider(messages)


async def echo_chat(messages: List[BaseMessage]) -> str:
    return f"Echo: {messages[-1].content}"


def ollama_options() -> dict:
    return {
        "num_ctx": int(os.getenv("OLLAMA_NUM_CTX", "1024")),
        "num_predict": int(os.getenv("OLLAMA_NUM_PREDICT", "256")),
        "temperature": float(os.getenv("OLLAMA_TEMPERATURE", "0.2")),
    }


def ollama_base_url() -> str:
    return os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")


def ollama_model() -> str:
    return os.getenv("OLLAMA_MODEL", OLLAMA_DEFAULT_MODEL)


def ollama_payload(messages: List[BaseMessage]) -> dict:
    return {
        "model": ollama_model(),
        "messages": [
            {"role": ollama_role(message), "content": message.content} for message in messages
        ],
        "stream": False,
        "options": ollama_options(),
    }


def ollama_role(message: BaseMessage) -> str:
    if message.type == "human":
        return "user"
    if message.type == "ai":
        return "assistant"
    if message.type == "system":
        return "system"
    return "user"


async def ollama_chat(messages: List[BaseMessage]) -> str:
    base_url = ollama_base_url()
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/api/chat",
                json=ollama_payload(messages),
                timeout=float(os.getenv("OLLAMA_TIMEOUT", "120")),
            )
    except httpx.ConnectError as ex:
        raise RuntimeError(f"Could not connect to Ollama at {base_url}") from ex

    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as ex:
        if response.status_code == 404:
            raise RuntimeError(
                f"Ollama model not found: {ollama_model()}. Run: ollama pull {ollama_model()}"
            ) from ex
        raise RuntimeError(f"Ollama request failed: HTTP {response.status_code}") from ex
    content = response.json().get("message", {}).get("content")
    if not content:
        raise RuntimeError("Ollama returned an empty response")
    return content.strip()


async def beam_chat_messages(messages: List[BaseMessage]) -> str:
    return await beam_chat({"messages": [message_to_beam_dict(m) for m in messages]})


def message_to_beam_dict(message: BaseMessage) -> dict:
    return {"type": message.type, "data": message.dict()}


async def beam_chat(payload):
    async with httpx.AsyncClient() as client:
        response = await client.request(
            "POST",
            os.getenv("BEAM_URL"),
            headers={
                "Accept": "*/*",
                "Accept-Encoding": "gzip, deflate",
                "Authorization": f"Basic {os.getenv('BEAM_TOKEN')}",
                "Connection": "keep-alive",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=10000,
        )
    response.raise_for_status()
    out = response.json().get("message")
    return out.get("text").strip() if isinstance(out, dict) else out


async def azure_openai_chat(messages: List[BaseMessage], temperature: float = 0.0) -> str:
    base_url = os.getenv("AZURE_OPENAI_API_BASE", "").rstrip("/")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    if not base_url or not deployment or not api_version or not api_key:
        raise RuntimeError("Set Azure OpenAI env vars before using voice features")

    payload = {
        "messages": [
            {"role": ollama_role(message), "content": message.content} for message in messages
        ],
        "temperature": temperature,
    }
    url = f"{base_url}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers={"api-key": api_key}, json=payload, timeout=120)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()
