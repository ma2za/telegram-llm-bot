import logging
import os

from langchain.schema import HumanMessage, AIMessage

from telegram_smart_bots.shared.audio import transcribe_and_check
from telegram_smart_bots.shared.chat import azure_openai_chat
from telegram_smart_bots.shared.db.mongo import mongodb_manager
from telegram_smart_bots.shared.history.history import MongoDBChatMessageHistory

logger = logging.getLogger(__name__)


async def idea_chat(audio: bytes, user_id: int, duration: int):
    db = mongodb_manager.get_database(os.getenv("DB_NAME"))
    collection = db[os.getenv("COLLECTION_NAME")]
    try:
        transcript = await transcribe_and_check(audio, user_id, duration)
        query = HumanMessage(content=transcript)

        result = await collection.find_one(
            {"telegram_id": user_id}, {"current_session": 1}
        )
        session_name = "default" if result is None else result.get("current_session")
        history = MongoDBChatMessageHistory(os.getenv("DB_NAME"), user_id, session_name)

        result = await history.messages
        response = await azure_openai_chat(result + [query])
        await history.add_message(query)
        await history.add_message(AIMessage(content=response))

        reply_msg = response
    except Exception as ex:
        logger.error(ex)
        reply_msg = "😿"
    return reply_msg


async def switch(user_id, session_name):
    db = mongodb_manager.get_database(os.getenv("DB_NAME"))
    collection = db[os.getenv("COLLECTION_NAME")]

    try:
        await collection.update_one(
            {"telegram_id": user_id},
            {"$set": {"current_session": session_name}},
            upsert=True,
        )

        reply_msg = f"Switched to idea: {session_name}"
    except Exception as ex:
        logger.error(ex)
        reply_msg = "😿"
    return reply_msg


async def summarize(user_id):
    db = mongodb_manager.get_database(os.getenv("DB_NAME"))
    collection = db[os.getenv("COLLECTION_NAME")]

    try:
        result = await collection.find_one(
            {"telegram_id": user_id}, {"current_session": 1}
        )
        session_name = "default" if result is None else result.get("current_session")
        history = MongoDBChatMessageHistory(os.getenv("DB_NAME"), user_id, session_name)

        result = await history.messages
        query = HumanMessage(
            content="""Please summarize the refined idea that emerged from our brainstorming session
            and propose a title that captures the essence of this idea."""
        )

        response = await azure_openai_chat(result + [query])

        reply_msg = response
    except Exception as ex:
        logger.error(ex)
        reply_msg = "😿"
    return reply_msg
