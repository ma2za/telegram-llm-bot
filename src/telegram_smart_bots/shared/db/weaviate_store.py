import logging
import os

import weaviate
from langchain.vectorstores import Weaviate

logger = logging.getLogger(__name__)


class WeaviateStoreManager:
    def __init__(self, host, port):
        self.client = weaviate.Client(f"http://{host}:{port}")

    def get_database(self, index_name: str, text_key: str):
        if not self.client.schema.exists(index_name):
            self.client.schema.create_class(os.getenv("WEAVIATE_CLASS"))

        return Weaviate(
            client=self.client,
            index_name=index_name,
            text_key=text_key,
        )


store_manager = WeaviateStoreManager(
    host=os.getenv("WEAVIATE_HOST"), port=int(os.getenv("WEAVIATE_PORT"))
)
