import asyncio
import json
import logging
from typing import List

from langchain.schema import (
    BaseChatMessageHistory,
)
from langchain.schema.messages import BaseMessage, messages_from_dict, messages_to_dict
from pymongo import errors

from telegram_smart_bots.shared.db.mongo import mongodb_manager

logger = logging.getLogger(__name__)

DEFAULT_DBNAME = "chat_history"
DEFAULT_COLLECTION_NAME = "message_store"


class MongoDBChatMessageHistory(BaseChatMessageHistory):
    """Chat message history that stores history in MongoDB."""

    def __init__(self, database_name: str, user_id, session_id):
        self.db = mongodb_manager.get_database(database_name)
        self.user_id = user_id
        self.session_id = session_id
        self.collection = self.db["chats"]
        asyncio.run(self.collection.create_index(["UserId", "SessionId"]))

    @property
    async def messages(self) -> List[BaseMessage]:  # type: ignore
        """Retrieve the messages from MongoDB"""
        cursor = None
        try:
            cursor = await self.collection.find(
                {"UserId": self.user_id, "SessionId": self.session_id}
            )

        except errors.OperationFailure as ex:
            logger.error(ex)
        items = (
            [json.loads(document["History"]) for document in cursor] if cursor else []
        )
        messages = messages_from_dict(items)
        return messages

    async def add_message(self, message: BaseMessage) -> None:
        """Append the message to the record in MongoDB"""

        try:
            await self.collection.insert_one(
                {
                    "UserId": self.user_id,
                    "History": json.dumps(messages_to_dict([message])[0]),
                }
            )
        except errors.WriteError as err:
            logger.error(err)

    async def clear(self) -> None:
        """Clear session memory from MongoDB"""
        try:
            await self.collection.delete_many({"UserId": self.user_id})
        except errors.WriteError as err:
            logger.error(err)
