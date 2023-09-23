import logging
import os
from pathlib import Path

from minio import Minio

logger = logging.getLogger(__name__)


class MinioManager:
    def __init__(self, host, port):
        self.client = Minio(
            f"{host}:{port}",
            secure=False,
            access_key=os.getenv("MINIO_ROOT_USER"),
            secret_key=os.getenv("MINIO_ROOT_PASSWORD"),
        )
        self.bucket_name = os.getenv("BOT_NAME")
        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)
        Path(".tmp").mkdir(parents=True, exist_ok=True)

    def get_objects(
        self, user_id: int, session_id: str = None, object_name: str = None
    ):
        prefix = f"{user_id}/"
        if session_id is not None:
            prefix += f"{session_id}/"
            if object_name is not None:
                prefix += f"{object_name}"
        for obj in self.client.list_objects(
            self.bucket_name, prefix=prefix, recursive=True
        ):
            yield obj.object_name, self.get_object(obj.object_name)

    def get_object(self, object_name: str) -> bytes:
        try:
            response = self.client.get_object(self.bucket_name, object_name=object_name)
            file_bytes = response.data
        except Exception as ex:
            logger.error(ex)
            file_bytes = None
        finally:
            response.close()
            response.release_conn()
        return file_bytes

    async def put_object(self, object_name: str, file_bytes: bytes):
        name = Path(object_name).name
        temp_file = f".tmp/{name}"
        try:
            with open(temp_file, "wb") as binary_file:
                binary_file.write(file_bytes)

            self.client.fput_object(self.bucket_name, object_name, temp_file)
        except Exception as ex:
            logger.error(ex)
        finally:
            os.remove(temp_file)


minio_manager = MinioManager(
    host=os.getenv("MINIO_HOST"), port=int(os.getenv("MINIO_PORT"))
)
