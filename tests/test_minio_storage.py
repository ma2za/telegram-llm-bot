import os
import unittest
from unittest.mock import AsyncMock, patch

from telegram_llm_bot.shared.db.minio_storage import MinioStorage


class ClientContext:
    def __init__(self, client):
        self.client = client

    async def __aenter__(self):
        return self.client

    async def __aexit__(self, exc_type, exc, tb):
        return False


class Session:
    def __init__(self, client):
        self.client_object = client

    def client(self, **kwargs):
        self.kwargs = kwargs
        return ClientContext(self.client_object)


class MinioStorageTest(unittest.IsolatedAsyncioTestCase):
    async def test_put_object_uses_async_s3_client(self):
        client = AsyncMock()
        session = Session(client)
        storage = MinioStorage(session=session)

        with patch.dict(
            os.environ,
            {
                "MINIO_ENDPOINT_URL": "http://localhost:9000",
                "MINIO_ACCESS_KEY": "access",
                "MINIO_SECRET_KEY": "secret",
                "MINIO_BUCKET": "bucket",
            },
            clear=False,
        ):
            key = await storage.put_object("voice/1/default/file.oga", b"abc", "audio/ogg")

        self.assertEqual(key, "voice/1/default/file.oga")
        self.assertEqual(session.kwargs["endpoint_url"], "http://localhost:9000")
        client.head_bucket.assert_awaited_once_with(Bucket="bucket")
        client.put_object.assert_awaited_once_with(
            Bucket="bucket",
            Key="voice/1/default/file.oga",
            Body=b"abc",
            ContentType="audio/ogg",
        )

    async def test_requires_minio_env(self):
        storage = MinioStorage()

        with patch.dict(os.environ, {"BOT_NAME": "bot"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "MINIO_ENDPOINT_URL"):
                await storage.put_object("x", b"abc")


if __name__ == "__main__":
    unittest.main()
