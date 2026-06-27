import os
import unittest
from unittest.mock import AsyncMock, Mock, patch

from telegram_llm_bot.shared import chat
from telegram_llm_bot.shared.messages import AIMessage, HumanMessage, SystemMessage


class ProviderSelectionTest(unittest.TestCase):
    def test_selects_ollama(self):
        with patch.dict(os.environ, {"LLM_PROVIDER": "ollama"}, clear=False):
            self.assertIs(chat.get_chat_provider(), chat.ollama_chat)

    def test_selects_beam(self):
        with patch.dict(os.environ, {"LLM_PROVIDER": "beam"}, clear=False):
            self.assertIs(chat.get_chat_provider(), chat.beam_chat_messages)

    def test_unknown_provider_fails(self):
        with patch.dict(os.environ, {"LLM_PROVIDER": "missing"}, clear=False):
            with self.assertRaisesRegex(ValueError, "Unsupported LLM_PROVIDER"):
                chat.get_chat_provider()

    def test_missing_provider_fails(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "Set LLM_PROVIDER"):
                chat.get_chat_provider()


class OllamaPayloadTest(unittest.TestCase):
    def test_builds_low_ram_payload(self):
        messages = [
            SystemMessage(content="system"),
            HumanMessage(content="hello"),
            AIMessage(content="hi"),
        ]

        with patch.dict(
            os.environ,
            {
                "OLLAMA_MODEL": "qwen2.5:0.5b",
                "OLLAMA_NUM_CTX": "1024",
                "OLLAMA_NUM_PREDICT": "256",
                "OLLAMA_TEMPERATURE": "0.2",
            },
            clear=False,
        ):
            payload = chat.ollama_payload(messages)

        self.assertEqual(payload["model"], "qwen2.5:0.5b")
        self.assertFalse(payload["stream"])
        self.assertEqual(payload["options"]["num_ctx"], 1024)
        self.assertEqual(payload["options"]["num_predict"], 256)
        self.assertEqual(payload["options"]["temperature"], 0.2)
        self.assertEqual(
            payload["messages"],
            [
                {"role": "system", "content": "system"},
                {"role": "user", "content": "hello"},
                {"role": "assistant", "content": "hi"},
            ],
        )


class OllamaChatTest(unittest.IsolatedAsyncioTestCase):
    async def test_posts_to_ollama_chat_endpoint(self):
        response = Mock()
        response.json.return_value = {"message": {"content": "ok"}}
        response.raise_for_status.return_value = None

        client = AsyncMock()
        client.__aenter__.return_value = client
        client.post.return_value = response

        with patch.dict(
            os.environ,
            {"OLLAMA_BASE_URL": "http://localhost:11434", "OLLAMA_MODEL": "qwen2.5:0.5b"},
            clear=False,
        ):
            with patch("telegram_llm_bot.shared.chat.httpx.AsyncClient", return_value=client):
                result = await chat.ollama_chat([HumanMessage(content="hello")])

        self.assertEqual(result, "ok")
        client.post.assert_awaited_once()
        url = client.post.await_args.kwargs.get("url") or client.post.await_args.args[0]
        self.assertEqual(url, "http://localhost:11434/api/chat")
        self.assertFalse(client.post.await_args.kwargs["json"]["stream"])


if __name__ == "__main__":
    unittest.main()
