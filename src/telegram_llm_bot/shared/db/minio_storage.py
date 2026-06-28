import logging
import os

import aioboto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class MinioStorage:
    def __init__(self, session=None):
        self.session = session or aioboto3.Session()

    def bucket_name(self) -> str:
        bucket = os.getenv("MINIO_BUCKET") or os.getenv("BOT_NAME")
        if not bucket:
            raise RuntimeError("Set MINIO_BUCKET or BOT_NAME before using object storage")
        return bucket

    def client_kwargs(self) -> dict:
        endpoint_url = os.getenv("MINIO_ENDPOINT_URL")
        access_key = os.getenv("MINIO_ACCESS_KEY") or os.getenv("MINIO_ROOT_USER")
        secret_key = os.getenv("MINIO_SECRET_KEY") or os.getenv("MINIO_ROOT_PASSWORD")
        if not endpoint_url or not access_key or not secret_key:
            raise RuntimeError(
                "Set MINIO_ENDPOINT_URL, MINIO_ACCESS_KEY, and MINIO_SECRET_KEY "
                "before using object storage"
            )
        return {
            "service_name": "s3",
            "endpoint_url": endpoint_url,
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
        }

    async def ensure_bucket(self, client, bucket: str) -> None:
        try:
            await client.head_bucket(Bucket=bucket)
        except ClientError as ex:
            code = str(ex.response.get("Error", {}).get("Code", ""))
            if code not in {"404", "NoSuchBucket", "NotFound"}:
                raise
            await client.create_bucket(Bucket=bucket)

    async def put_object(
        self,
        object_name: str,
        file_bytes: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        bucket = self.bucket_name()
        async with self.session.client(**self.client_kwargs()) as client:
            await self.ensure_bucket(client, bucket)
            await client.put_object(
                Bucket=bucket,
                Key=object_name,
                Body=file_bytes,
                ContentType=content_type,
            )
        return object_name

    async def get_object(self, object_name: str) -> bytes:
        bucket = self.bucket_name()
        async with self.session.client(**self.client_kwargs()) as client:
            response = await client.get_object(Bucket=bucket, Key=object_name)
            body = response["Body"]
            try:
                return await body.read()
            finally:
                body.close()


minio_storage = MinioStorage()
