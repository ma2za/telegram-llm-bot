import itertools
import logging
import os

from langchain.schema import HumanMessage, AIMessage, SystemMessage

from telegram_llm_bot.shared.audio import transcribe_and_check
from telegram_llm_bot.shared.chat import azure_openai_chat
from telegram_llm_bot.shared.db.mongo import mongodb_manager
from telegram_llm_bot.shared.history.history import MongoDBChatMessageHistory

logger = logging.getLogger(__name__)


async def new_note(audio: bytes, user_id: int, duration: int) -> str:
    db = mongodb_manager.get_database(os.getenv("BOT_NAME"))
    collection = db[os.getenv("COLLECTION_NAME")]
    try:
        transcript = await transcribe_and_check(audio, user_id, duration)
        query = HumanMessage(content=transcript)

        result = await collection.find_one({"user_id": user_id}, {"current_session": 1})
        session_name = "default" if result is None else result.get("current_session")
        chat_history = MongoDBChatMessageHistory(
            os.getenv("BOT_NAME"), user_id, session_name
        )

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
    db = mongodb_manager.get_database(os.getenv("BOT_NAME"))
    collection = db[os.getenv("COLLECTION_NAME")]

    try:
        await collection.update_one(
            {"user_id": user_id},
            {"$set": {"current_session": session_name}},
            upsert=True,
        )

        reply_msg = f"Switched to note: {session_name}"
    except Exception as ex:
        logger.error(ex)
        reply_msg = "😿"
    return reply_msg


async def summarize(user_id: int) -> str:
    db = mongodb_manager.get_database(os.getenv("BOT_NAME"))
    collection = db[os.getenv("COLLECTION_NAME")]

    try:
        result = await collection.find_one({"user_id": user_id}, {"current_session": 1})
        session_name = "default" if result is None else result.get("current_session")
        history = MongoDBChatMessageHistory(
            os.getenv("BOT_NAME"), user_id, session_name
        )

        result = await history.messages
        query = HumanMessage(
            content="""Please summarize the notes that emerged from our brainstorming session
            and propose a title that captures the essence of this conversation."""
        )

        response = await azure_openai_chat(
            list(itertools.chain.from_iterable(dict(result).values())) + [query]
        )

        reply_msg = response
    except Exception as ex:
        logger.error(ex)
        reply_msg = "😿"
    return reply_msg
