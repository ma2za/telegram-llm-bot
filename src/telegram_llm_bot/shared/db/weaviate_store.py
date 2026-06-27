import logging
import os

logger = logging.getLogger(__name__)


class WeaviateStoreManager:
    def __init__(self, host, port):
        import weaviate

        self.client = weaviate.Client(f"http://{host}:{port}")

    def get_database(self, index_name: str, text_key: str):
        from langchain.vectorstores import Weaviate

        if not self.client.schema.exists(index_name):
            self.client.schema.create_class(os.getenv("WEAVIATE_CLASS"))

        return Weaviate(
            client=self.client,
            index_name=index_name,
            text_key=text_key,
        )


def get_store_manager():
    if not os.getenv("WEAVIATE_HOST") or not os.getenv("WEAVIATE_PORT"):
        raise RuntimeError("Set WEAVIATE_HOST and WEAVIATE_PORT before using Weaviate")
    return WeaviateStoreManager(
        host=os.getenv("WEAVIATE_HOST"), port=int(os.getenv("WEAVIATE_PORT"))
    )
