import logging
from typing import List

from langchain.schema import (
    BaseChatMessageHistory,
)
from langchain.schema.messages import BaseMessage, messages_from_dict, messages_to_dict
from pymongo import errors

from telegram_smart_bots.shared.db.mongo import mongodb_manager

logger = logging.getLogger(__name__)


class MongoDBChatMessageHistory(BaseChatMessageHistory):
    """Chat message history that stores history in MongoDB."""

    index_created: bool = False

    def __init__(
        self,
        database_name: str,
        user_id: int,
        session_id: str,
        history_field: str = "History",
    ):
        self.db = mongodb_manager.get_database(database_name)
        self.collection = self.db["chats"]
        self.history_field = history_field
        self.user_id = user_id
        self.session_id = session_id

    async def setup(self):
        await self.collection.create_index(["user_id", "session_id"])

    @property
    async def messages(self) -> List[BaseMessage]:
        """Retrieve the messages from MongoDB"""
        # TODO I don't like that
        if not MongoDBChatMessageHistory.index_created:
            await self.setup()
            MongoDBChatMessageHistory.index_created = True
        items = await self.collection.find_one(
            {"user_id": self.user_id, "session_id": self.session_id},
            {self.history_field: 1},
        )
        if items is None:
            messages = []
        else:
            messages = messages_from_dict(items.get(self.history_field))
        return messages

    async def add_messages(self, messages: List[BaseMessage]) -> None:
        try:
            await self.collection.update_one(
                {"user_id": self.user_id, "session_id": self.session_id},
                {"$push": {self.history_field: {"$each": messages_to_dict(messages)}}},
                upsert=True,
            )
        except errors.WriteError as err:
            logger.error(err)

    async def add_message(self, message: BaseMessage) -> None:
        """Append the message to the record in MongoDB"""
        await self.add_messages([message])

    async def clear(self) -> None:
        """Clear session memory from MongoDB"""
        try:
            await self.collection.delete_many({"user_id": self.user_id})
        except errors.WriteError as err:
            logger.error(err)
