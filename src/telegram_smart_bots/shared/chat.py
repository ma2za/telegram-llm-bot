import logging
import os
from typing import List

import httpx
from langchain.chat_models import AzureChatOpenAI
from langchain.schema import BaseMessage

logger = logging.getLogger(__name__)


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


async def azure_openai_chat(
    messages: List[BaseMessage], temperature: float = 0.1
) -> str:
    llm = AzureChatOpenAI(
        openai_api_type=os.getenv("AZURE_OPENAI_API_TYPE"),
        openai_api_base=os.getenv("AZURE_OPENAI_API_BASE"),
        openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        streaming=False,
        temperature=temperature,
    )
    result = await llm._call_async(messages)
    return result.content
