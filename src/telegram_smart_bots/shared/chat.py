import logging
import os

import httpx
from langchain import LLMChain
from langchain.chat_models import AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain.schema import SystemMessage

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


async def azure_openai_chat(text: str, temperature: float = 0.1):
    llm = AzureChatOpenAI(
        openai_api_type=os.getenv("AZURE_OPENAI_API_TYPE"),
        openai_api_base=os.getenv("AZURE_OPENAI_API_BASE"),
        openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        streaming=False,
        temperature=temperature,
    )
    messages = [
        SystemMessage(
            content="""Edit, enhance, and refine the following text to resemble a travel journal
            infused with the spirit of Hunter S. Thompson. Maintain the original content, style,
            and language while improving readability. Embrace the chaotic and adventurous tone,
            and do not invent events or details not present in the original text.
            Preserve any curse words and the speaker's unique voice."""
        ),
        HumanMessagePromptTemplate.from_template("Text: {text}"),
    ]

    chain = LLMChain(llm=llm, prompt=ChatPromptTemplate(messages=messages))
    result = await chain.arun(text)
    return result
