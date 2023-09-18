import logging
import os

from langchain.schema import HumanMessage, AIMessage, SystemMessage

from telegram_smart_bots.shared.audio import transcribe_and_check
from telegram_smart_bots.shared.chat import azure_openai_chat
from telegram_smart_bots.shared.db.mongo import mongodb_manager
from telegram_smart_bots.shared.history.history import MongoDBChatMessageHistory

logger = logging.getLogger(__name__)


async def idea_chat(audio: bytes, user_id: int, duration: int) -> str:
    db = mongodb_manager.get_database(os.getenv("DB_NAME"))
    collection = db[os.getenv("COLLECTION_NAME")]
    try:
        transcript = await transcribe_and_check(audio, user_id, duration)
        query = HumanMessage(content=transcript)

        result = await collection.find_one(
            {"telegram_id": user_id}, {"current_session": 1}
        )
        session_name = "default" if result is None else result.get("current_session")
        chat_history = MongoDBChatMessageHistory(
            os.getenv("DB_NAME"), user_id, session_name
        )
        # await chat_history.clear()
        messages = await chat_history.messages
        new_messages = []
        if not messages:
            new_messages.append(
                SystemMessage(
                    content="""Let's have a brainstorming session to refine and explore an idea.
            I'll start by describing the initial concept, and then we can go
            back and forth to discuss and develop it. Feel free to ask
            questions and provide suggestions as we go along. The idea has to start from me, so just wait until
            I give you something that looks like an idea, ignore any other request."""
                )
            )
        new_messages.append(query)
        response = await azure_openai_chat(messages + new_messages)
        new_messages.append(AIMessage(content=response))
        await chat_history.add_messages(new_messages)

        reply_msg = response
    except Exception as ex:
        logger.error(ex)
        reply_msg = "😿"
    return reply_msg


async def switch(user_id: int, session_name: str) -> str:
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


async def summarize(user_id: int) -> str:
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