import logging
import os
import json
import sqlite3
import time
from contextlib import closing
from pathlib import Path
from typing import List, Sequence, Dict

from pymongo import errors

from telegram_llm_bot.paths import PROJECT_DIR
from telegram_llm_bot.shared.db.mongo import mongodb_manager
from telegram_llm_bot.shared.messages import BaseMessage, messages_from_dict

logger = logging.getLogger(__name__)
DEFAULT_SESSION_ID = "default"


def get_chat_history(database_name: str, user_id: int, session_id: str = None):
    backend = os.getenv("CHAT_HISTORY_BACKEND", "sqlite").strip().lower()
    if backend == "sqlite":
        return SQLiteChatMessageHistory(database_name, user_id, session_id)
    if backend == "memory":
        return InMemoryChatMessageHistory(database_name, user_id, session_id)
    if backend == "mongo":
        return MongoDBChatMessageHistory(database_name, user_id, session_id)
    raise ValueError(f"Unsupported CHAT_HISTORY_BACKEND: {backend}")


def get_session_store(database_name: str, user_id: int):
    backend = os.getenv("CHAT_HISTORY_BACKEND", "sqlite").strip().lower()
    if backend == "sqlite":
        return SQLiteChatSessionStore(database_name, user_id)
    if backend == "memory":
        return InMemoryChatSessionStore(database_name, user_id)
    if backend == "mongo":
        return MongoDBChatSessionStore(database_name, user_id)
    raise ValueError(f"Unsupported CHAT_HISTORY_BACKEND: {backend}")


async def get_active_session(database_name: str, user_id: int) -> str:
    return await get_session_store(database_name, user_id).get_active_session()


async def set_active_session(database_name: str, user_id: int, session_id: str) -> None:
    await get_session_store(database_name, user_id).set_active_session(session_id)


async def list_sessions(database_name: str, user_id: int) -> List[str]:
    return await get_session_store(database_name, user_id).list_sessions()


async def delete_session(database_name: str, user_id: int, session_id: str) -> bool:
    return await get_session_store(database_name, user_id).delete_session(session_id)


async def clear_user_sessions(database_name: str, user_id: int) -> None:
    await get_session_store(database_name, user_id).clear_user_sessions()


class SQLiteChatMessageHistory:
    def __init__(self, database_name: str, user_id: int, session_id: str = None):
        self.database_name = database_name
        self.user_id = user_id
        self.session_id = session_id
        self.session_key = session_id or ""
        self.path = self._database_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.setup()

    @staticmethod
    def _database_path():
        configured = os.getenv("SQLITE_HISTORY_PATH", ".tmp/chat_history.sqlite3")
        path = Path(configured)
        return path if path.is_absolute() else PROJECT_DIR / path

    @staticmethod
    def _message_to_dict(message: BaseMessage) -> dict:
        return {"type": message.type, "data": message.dict()}

    @staticmethod
    def _timestamp_key(message: BaseMessage) -> str:
        timestamp = message.additional_kwargs.get("timestamp")
        return str(timestamp if timestamp is not None else time.time_ns())

    @staticmethod
    def _sort_key(timestamp_key: str) -> float:
        try:
            return float(timestamp_key)
        except ValueError:
            return float(time.time_ns())

    def messages_to_dict(self, messages: Sequence[BaseMessage]) -> Dict[str, dict]:
        return {f"History.{self._timestamp_key(m)}": self._message_to_dict(m) for m in messages}

    def setup(self):
        with closing(sqlite3.connect(self.path)) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    database_name TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    session_id TEXT NOT NULL,
                    timestamp_key TEXT NOT NULL,
                    sort_key REAL NOT NULL,
                    message_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    message_json TEXT NOT NULL,
                    UNIQUE(database_name, user_id, session_id, timestamp_key)
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS chat_messages_lookup
                ON chat_messages(database_name, user_id, session_id, sort_key, id)
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    database_name TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    session_id TEXT NOT NULL,
                    updated_at REAL NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY(database_name, user_id, session_id)
                )
                """
            )
            conn.commit()

    @property
    async def messages(self):
        with closing(sqlite3.connect(self.path)) as conn:
            rows = conn.execute(
                """
                SELECT message_json
                FROM chat_messages
                WHERE database_name = ? AND user_id = ? AND session_id = ?
                ORDER BY sort_key, id
                """,
                (self.database_name, self.user_id, self.session_key),
            ).fetchall()
        yield self.session_id, messages_from_dict([json.loads(row[0]) for row in rows])

    async def add_messages(self, messages: List[BaseMessage]) -> None:
        records = []
        for message in messages:
            timestamp_key = self._timestamp_key(message)
            records.append(
                (
                    self.database_name,
                    self.user_id,
                    self.session_key,
                    timestamp_key,
                    self._sort_key(timestamp_key),
                    message.type,
                    message.content,
                    json.dumps(message.additional_kwargs),
                    json.dumps(self._message_to_dict(message)),
                )
            )
        with closing(sqlite3.connect(self.path)) as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO chat_messages (
                    database_name,
                    user_id,
                    session_id,
                    timestamp_key,
                    sort_key,
                    message_type,
                    content,
                    metadata_json,
                    message_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                records,
            )
            conn.commit()

    async def add_message(self, message: BaseMessage) -> None:
        await self.add_messages([message])

    async def clear(self) -> None:
        with closing(sqlite3.connect(self.path)) as conn:
            conn.execute(
                """
                DELETE FROM chat_messages
                WHERE database_name = ? AND user_id = ? AND session_id = ?
                """,
                (self.database_name, self.user_id, self.session_key),
            )
            conn.commit()


class InMemoryChatMessageHistory:
    histories = {}

    def __init__(self, database_name: str, user_id: int, session_id: str = None):
        self.key = (database_name, user_id, session_id)

    @staticmethod
    def _message_to_dict(message: BaseMessage) -> dict:
        return {"type": message.type, "data": message.dict()}

    def messages_to_dict(self, messages: Sequence[BaseMessage]) -> Dict[str, dict]:
        return {
            f"History.{m.additional_kwargs.get('timestamp')}": self._message_to_dict(m)
            for m in messages
        }

    @property
    async def messages(self):
        yield self.key[2], self.histories.get(self.key, [])

    async def add_messages(self, messages: List[BaseMessage]) -> None:
        history = self.histories.setdefault(self.key, [])
        history.extend(messages)

    async def add_message(self, message: BaseMessage) -> None:
        await self.add_messages([message])

    async def clear(self) -> None:
        self.histories.pop(self.key, None)


class SQLiteChatSessionStore:
    def __init__(self, database_name: str, user_id: int):
        self.database_name = database_name
        self.user_id = user_id
        self.path = SQLiteChatMessageHistory._database_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        SQLiteChatMessageHistory(database_name, user_id).setup()

    def _touch_session(self, conn, session_id: str, is_active: bool = False):
        conn.execute(
            """
            INSERT INTO chat_sessions(database_name, user_id, session_id, updated_at, is_active)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(database_name, user_id, session_id)
            DO UPDATE SET updated_at = excluded.updated_at
            """,
            (self.database_name, self.user_id, session_id, time.time(), int(is_active)),
        )

    async def get_active_session(self) -> str:
        with closing(sqlite3.connect(self.path)) as conn:
            row = conn.execute(
                """
                SELECT session_id
                FROM chat_sessions
                WHERE database_name = ? AND user_id = ? AND is_active = 1
                ORDER BY updated_at DESC
                LIMIT 1
                """,
                (self.database_name, self.user_id),
            ).fetchone()
            if row:
                return row[0]
            self._touch_session(conn, DEFAULT_SESSION_ID, is_active=True)
            conn.execute(
                """
                UPDATE chat_sessions
                SET is_active = CASE WHEN session_id = ? THEN 1 ELSE 0 END
                WHERE database_name = ? AND user_id = ?
                """,
                (DEFAULT_SESSION_ID, self.database_name, self.user_id),
            )
            conn.commit()
        return DEFAULT_SESSION_ID

    async def set_active_session(self, session_id: str) -> None:
        with closing(sqlite3.connect(self.path)) as conn:
            self._touch_session(conn, session_id, is_active=True)
            conn.execute(
                """
                UPDATE chat_sessions
                SET is_active = CASE WHEN session_id = ? THEN 1 ELSE 0 END
                WHERE database_name = ? AND user_id = ?
                """,
                (session_id, self.database_name, self.user_id),
            )
            conn.commit()

    async def list_sessions(self) -> List[str]:
        await self.get_active_session()
        with closing(sqlite3.connect(self.path)) as conn:
            rows = conn.execute(
                """
                SELECT session_id
                FROM chat_sessions
                WHERE database_name = ? AND user_id = ?
                ORDER BY updated_at DESC, session_id
                """,
                (self.database_name, self.user_id),
            ).fetchall()
        return [row[0] for row in rows]

    async def delete_session(self, session_id: str) -> bool:
        with closing(sqlite3.connect(self.path)) as conn:
            exists = conn.execute(
                """
                SELECT 1
                FROM chat_sessions
                WHERE database_name = ? AND user_id = ? AND session_id = ?
                """,
                (self.database_name, self.user_id, session_id),
            ).fetchone()
            if not exists:
                return False
            conn.execute(
                """
                DELETE FROM chat_messages
                WHERE database_name = ? AND user_id = ? AND session_id = ?
                """,
                (self.database_name, self.user_id, session_id),
            )
            conn.execute(
                """
                DELETE FROM chat_sessions
                WHERE database_name = ? AND user_id = ? AND session_id = ?
                """,
                (self.database_name, self.user_id, session_id),
            )
            conn.commit()
        if session_id == await self.get_active_session():
            await self.set_active_session(DEFAULT_SESSION_ID)
        return True

    async def clear_user_sessions(self) -> None:
        with closing(sqlite3.connect(self.path)) as conn:
            conn.execute(
                "DELETE FROM chat_messages WHERE database_name = ? AND user_id = ?",
                (self.database_name, self.user_id),
            )
            conn.execute(
                "DELETE FROM chat_sessions WHERE database_name = ? AND user_id = ?",
                (self.database_name, self.user_id),
            )
            conn.commit()
        await self.set_active_session(DEFAULT_SESSION_ID)


class InMemoryChatSessionStore:
    active = {}

    def __init__(self, database_name: str, user_id: int):
        self.key = (database_name, user_id)

    async def get_active_session(self) -> str:
        return self.active.setdefault(self.key, DEFAULT_SESSION_ID)

    async def set_active_session(self, session_id: str) -> None:
        self.active[self.key] = session_id

    async def list_sessions(self) -> List[str]:
        sessions = {
            key[2]
            for key in InMemoryChatMessageHistory.histories
            if key[0] == self.key[0] and key[1] == self.key[1] and key[2]
        }
        sessions.add(await self.get_active_session())
        return sorted(sessions)

    async def delete_session(self, session_id: str) -> bool:
        keys = [
            key
            for key in InMemoryChatMessageHistory.histories
            if key[0] == self.key[0] and key[1] == self.key[1] and key[2] == session_id
        ]
        exists = bool(keys) or self.active.get(self.key) == session_id
        for key in keys:
            InMemoryChatMessageHistory.histories.pop(key, None)
        if self.active.get(self.key) == session_id:
            self.active[self.key] = DEFAULT_SESSION_ID
        return exists

    async def clear_user_sessions(self) -> None:
        keys = [
            key
            for key in InMemoryChatMessageHistory.histories
            if key[0] == self.key[0] and key[1] == self.key[1]
        ]
        for key in keys:
            InMemoryChatMessageHistory.histories.pop(key, None)
        self.active[self.key] = DEFAULT_SESSION_ID


class MongoDBChatMessageHistory:
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
            yield c.get("session_id"), messages_from_dict(list(c.get("History", {}).values()))

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


class MongoDBChatSessionStore:
    def __init__(self, database_name: str, user_id: int):
        self.db = mongodb_manager.get_database(database_name)
        self.collection = self.db["chat_sessions"]
        self.history = self.db["chats"]
        self.user_id = user_id

    async def get_active_session(self) -> str:
        row = await self.collection.find_one({"user_id": self.user_id, "is_active": True})
        if row:
            return row["session_id"]
        await self.set_active_session(DEFAULT_SESSION_ID)
        return DEFAULT_SESSION_ID

    async def set_active_session(self, session_id: str) -> None:
        await self.collection.update_many({"user_id": self.user_id}, {"$set": {"is_active": False}})
        await self.collection.update_one(
            {"user_id": self.user_id, "session_id": session_id},
            {"$set": {"is_active": True, "updated_at": time.time()}},
            upsert=True,
        )

    async def list_sessions(self) -> List[str]:
        await self.get_active_session()
        cursor = self.collection.find({"user_id": self.user_id}).sort("updated_at", -1)
        return [row["session_id"] async for row in cursor]

    async def delete_session(self, session_id: str) -> bool:
        result = await self.collection.delete_one(
            {"user_id": self.user_id, "session_id": session_id}
        )
        await self.history.delete_many({"user_id": self.user_id, "session_id": session_id})
        if session_id == await self.get_active_session():
            await self.set_active_session(DEFAULT_SESSION_ID)
        return result.deleted_count > 0

    async def clear_user_sessions(self) -> None:
        await self.collection.delete_many({"user_id": self.user_id})
        await self.history.delete_many({"user_id": self.user_id})
        await self.set_active_session(DEFAULT_SESSION_ID)
