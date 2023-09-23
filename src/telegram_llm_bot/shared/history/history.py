import logging
from typing import List, Sequence, Dict

from langchain.schema import (
    BaseChatMessageHistory,
)
from langchain.schema.messages import BaseMessage, messages_from_dict
from pymongo import errors

from telegram_llm_bot.shared.db.mongo import mongodb_manager

logger = logging.getLogger(__name__)


class MongoDBChatMessageHistory(BaseChatMessageHistory):
    """Chat message history that stores history in MongoDB."""

    index_created: bool = False

    def __init__(self, database_name: str, user_id: int, session_id: str = None):
        self.db = mongodb_manager.get_database(database_name)
        self.collection = self.db["chats"]
        self.user_id = user_id
        self.session_id = session_id

    @staticmethod
    def _message_to_dict(message: BaseMessage) -> dict:
        return {"type": message.type, "data": message.dict()}

    def messages_to_dict(self, messages: Sequence[BaseMessage]) -> Dict[str, dict]:
        return {
            f"History.{m.additional_kwargs.get('timestamp')}": self._message_to_dict(m)
            for m in messages
        }

    async def setup(self):
        await self.collection.create_index(["user_id", "session_id"])

    @property
    async def messages(self):
        """Retrieve the messages from MongoDB"""
        # TODO I don't like that
        # if not MongoDBChatMessageHistory.index_created:
        #     await self.setup()
        #     MongoDBChatMessageHistory.index_created = True
        filters = {"user_id": self.user_id}
        if self.session_id is not None:
            filters["session_id"] = self.session_id
        cursor = self.collection.find(filters)
        async for c in cursor:
            yield c.get("session_id"), messages_from_dict(
                list(c.get("History", {}).values())
            )

    async def add_messages(self, messages: List[BaseMessage]) -> None:
        try:
            await self.collection.update_one(
                {"user_id": self.user_id, "session_id": self.session_id},
                {"$set": self.messages_to_dict(messages)},
                upsert=True,
            )
        except errors.WriteError as err:
            logger.error(err)

    async def add_message(self, message: BaseMessage) -> None:
        """Append the message to the record in MongoDB"""
        await self.add_messages([message])

    async def remove_message(self, key: str) -> None:
        try:
            await self.collection.update_one(
                {"user_id": self.user_id, "session_id": self.session_id},
                {"$unset": {f"History.{key}": ""}},
                upsert=True,
            )
        except errors.WriteError as err:
            logger.error(err)

    async def clear(self) -> None:
        """Clear session memory from MongoDB"""
        try:
            await self.collection.delete_many({"user_id": self.user_id})
        except errors.WriteError as err:
            logger.error(err)
