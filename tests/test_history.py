import os
import tempfile
import unittest
from unittest.mock import patch

from telegram_llm_bot.shared.history.history import (
    DEFAULT_SESSION_ID,
    InMemoryChatMessageHistory,
    MongoDBChatMessageHistory,
    SQLiteChatMessageHistory,
    delete_session,
    get_active_session,
    get_chat_history,
    list_sessions,
    set_active_session,
    clear_user_sessions,
)
from telegram_llm_bot.shared.messages import AIMessage, HumanMessage


class HistoryBackendSelectionTest(unittest.TestCase):
    def test_selects_sqlite(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(
                os.environ,
                {
                    "CHAT_HISTORY_BACKEND": "sqlite",
                    "SQLITE_HISTORY_PATH": f"{directory}/history.sqlite3",
                },
                clear=False,
            ):
                history = get_chat_history("bot", 1)

        self.assertIsInstance(history, SQLiteChatMessageHistory)

    def test_selects_memory(self):
        with patch.dict(os.environ, {"CHAT_HISTORY_BACKEND": "memory"}, clear=False):
            history = get_chat_history("bot", 1)

        self.assertIsInstance(history, InMemoryChatMessageHistory)

    def test_selects_mongo(self):
        with patch.dict(
            os.environ,
            {
                "CHAT_HISTORY_BACKEND": "mongo",
                "MONGO_HOST": "localhost",
                "MONGO_PORT": "27017",
            },
            clear=False,
        ):
            history = get_chat_history("bot", 1)

        self.assertIsInstance(history, MongoDBChatMessageHistory)

    def test_unknown_backend_fails(self):
        with patch.dict(os.environ, {"CHAT_HISTORY_BACKEND": "missing"}, clear=False):
            with self.assertRaisesRegex(ValueError, "Unsupported CHAT_HISTORY_BACKEND"):
                get_chat_history("bot", 1)


class SQLiteHistoryTest(unittest.IsolatedAsyncioTestCase):
    async def test_persists_messages_across_instances(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(
                os.environ,
                {
                    "CHAT_HISTORY_BACKEND": "sqlite",
                    "SQLITE_HISTORY_PATH": f"{directory}/history.sqlite3",
                },
                clear=False,
            ):
                history = SQLiteChatMessageHistory("bot", 1)
                await history.add_messages(
                    [
                        HumanMessage(content="hello", additional_kwargs={"timestamp": 1}),
                        AIMessage(content="hi", additional_kwargs={"timestamp": 2}),
                    ]
                )

                reloaded = SQLiteChatMessageHistory("bot", 1)
                messages = [message async for _, values in reloaded.messages for message in values]

        self.assertEqual([message.content for message in messages], ["hello", "hi"])

    async def test_clear_removes_only_selected_user_session(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(
                os.environ,
                {
                    "CHAT_HISTORY_BACKEND": "sqlite",
                    "SQLITE_HISTORY_PATH": f"{directory}/history.sqlite3",
                },
                clear=False,
            ):
                selected = SQLiteChatMessageHistory("bot", 1, "a")
                other_session = SQLiteChatMessageHistory("bot", 1, "b")
                other_user = SQLiteChatMessageHistory("bot", 2, "a")

                await selected.add_message(
                    HumanMessage(content="selected", additional_kwargs={"timestamp": 1})
                )
                await other_session.add_message(
                    HumanMessage(content="other session", additional_kwargs={"timestamp": 2})
                )
                await other_user.add_message(
                    HumanMessage(content="other user", additional_kwargs={"timestamp": 3})
                )
                await selected.clear()

                selected_messages = [
                    message async for _, values in selected.messages for message in values
                ]
                other_session_messages = [
                    message async for _, values in other_session.messages for message in values
                ]
                other_user_messages = [
                    message async for _, values in other_user.messages for message in values
                ]

        self.assertEqual(selected_messages, [])
        self.assertEqual([message.content for message in other_session_messages], ["other session"])
        self.assertEqual([message.content for message in other_user_messages], ["other user"])

    async def test_default_active_session(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(
                os.environ,
                {
                    "CHAT_HISTORY_BACKEND": "sqlite",
                    "SQLITE_HISTORY_PATH": f"{directory}/history.sqlite3",
                },
                clear=False,
            ):
                session = await get_active_session("bot", 1)

        self.assertEqual(session, DEFAULT_SESSION_ID)

    async def test_set_and_list_sessions(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(
                os.environ,
                {
                    "CHAT_HISTORY_BACKEND": "sqlite",
                    "SQLITE_HISTORY_PATH": f"{directory}/history.sqlite3",
                },
                clear=False,
            ):
                await set_active_session("bot", 1, "work")
                await set_active_session("bot", 1, "ideas")

                active = await get_active_session("bot", 1)
                sessions = await list_sessions("bot", 1)

        self.assertEqual(active, "ideas")
        self.assertEqual(set(sessions), {"work", "ideas"})

    async def test_delete_session_removes_only_selected_user_session(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(
                os.environ,
                {
                    "CHAT_HISTORY_BACKEND": "sqlite",
                    "SQLITE_HISTORY_PATH": f"{directory}/history.sqlite3",
                },
                clear=False,
            ):
                await set_active_session("bot", 1, "work")
                await set_active_session("bot", 2, "work")
                selected = SQLiteChatMessageHistory("bot", 1, "work")
                other_user = SQLiteChatMessageHistory("bot", 2, "work")
                await selected.add_message(
                    HumanMessage(content="selected", additional_kwargs={"timestamp": 1})
                )
                await other_user.add_message(
                    HumanMessage(content="other", additional_kwargs={"timestamp": 2})
                )

                deleted = await delete_session("bot", 1, "work")
                selected_messages = [
                    message async for _, values in selected.messages for message in values
                ]
                other_user_messages = [
                    message async for _, values in other_user.messages for message in values
                ]

        self.assertTrue(deleted)
        self.assertEqual(selected_messages, [])
        self.assertEqual([message.content for message in other_user_messages], ["other"])

    async def test_clear_user_sessions_removes_all_user_sessions(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(
                os.environ,
                {
                    "CHAT_HISTORY_BACKEND": "sqlite",
                    "SQLITE_HISTORY_PATH": f"{directory}/history.sqlite3",
                },
                clear=False,
            ):
                await set_active_session("bot", 1, "work")
                await set_active_session("bot", 1, "ideas")
                await SQLiteChatMessageHistory("bot", 1, "work").add_message(
                    HumanMessage(content="work", additional_kwargs={"timestamp": 1})
                )
                await SQLiteChatMessageHistory("bot", 1, "ideas").add_message(
                    HumanMessage(content="ideas", additional_kwargs={"timestamp": 2})
                )

                await clear_user_sessions("bot", 1)
                active = await get_active_session("bot", 1)
                sessions = await list_sessions("bot", 1)

        self.assertEqual(active, DEFAULT_SESSION_ID)
        self.assertEqual(sessions, [DEFAULT_SESSION_ID])


if __name__ == "__main__":
    unittest.main()
