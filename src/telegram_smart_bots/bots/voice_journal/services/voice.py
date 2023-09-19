import logging
import os
from datetime import date

from langchain.schema import HumanMessage, SystemMessage

from telegram_smart_bots.shared.audio import transcribe_and_check
from telegram_smart_bots.shared.chat import azure_openai_chat
from telegram_smart_bots.shared.db.mongo import mongodb_manager
from telegram_smart_bots.shared.history.history import MongoDBChatMessageHistory

logger = logging.getLogger(__name__)


async def voice_chat(audio: bytes, user_id: int, duration: int, msg_date: int) -> str:
    db = mongodb_manager.get_database(os.getenv("DB_NAME"))
    collection = db[os.getenv("COLLECTION_NAME")]
    try:
        transcript = await transcribe_and_check(audio, user_id, duration)

        result = await collection.find_one({"user_id": user_id}, {"editor": 1})
        edit = 1 if result is None else result.get("editor")

        chat_history = MongoDBChatMessageHistory(
            os.getenv("DB_NAME"), user_id, f"{date.fromtimestamp(msg_date)}", "messages"
        )

        if edit:
            messages = [
                SystemMessage(
                    content="""Edit, enhance, and refine the following text to resemble a travel journal infused
                    with a gonzo, vivid, truthful and outrageous style. Maintain the original content, style, and language while
                    improving readability. Embrace the chaotic and adventurous tone, and do not invent events or details
                    not present in the original text. Preserve any curse words and the speaker's unique voice."""
                ),
                HumanMessage(content=transcript),
            ]

            transcript = await azure_openai_chat(messages)
        response = HumanMessage(content=transcript)
        response.additional_kwargs["timestamp"] = msg_date
        await chat_history.add_message(response)

        reply_msg = response
    except Exception as ex:
        logger.error(ex)
        reply_msg = "😿"
    return reply_msg
