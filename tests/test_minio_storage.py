import os
import unittest
from unittest.mock import AsyncMock, patch

from botocore.exceptions import EndpointConnectionError

from telegram_llm_bot.shared.db.minio_storage import MinioStorage
from telegram_llm_bot.shared.readiness import FAIL, OK, WARN, check_minio_readiness


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

    async def test_minio_readiness_passes_when_configured_and_reachable(self):
        client = AsyncMock()
        storage = MinioStorage(session=Session(client))

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
            result = await check_minio_readiness(storage)

        self.assertEqual(result.severity, OK)
        self.assertEqual(result.message, "MinIO: reachable for bucket bucket")
        client.list_buckets.assert_awaited_once()

    async def test_minio_readiness_fails_when_env_is_missing(self):
        storage = MinioStorage()

        with patch.dict(os.environ, {"BOT_NAME": "bot"}, clear=True):
            result = await check_minio_readiness(storage)

        self.assertEqual(result.severity, FAIL)
        self.assertIn("MINIO_ENDPOINT_URL", result.message)

    async def test_minio_readiness_warns_when_endpoint_is_unreachable(self):
        client = AsyncMock()
        client.list_buckets.side_effect = EndpointConnectionError(endpoint_url="http://x")
        storage = MinioStorage(session=Session(client))

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
            result = await check_minio_readiness(storage)

        self.assertEqual(result.severity, WARN)
        self.assertEqual(result.message, "MinIO: unreachable for bucket bucket")


if __name__ == "__main__":
    unittest.main()
