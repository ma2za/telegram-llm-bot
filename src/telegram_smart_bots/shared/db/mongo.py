import logging
import os

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

logger = logging.getLogger(__name__)


class MongoDBManager:
    def __init__(self, host, port):
        self.client = AsyncIOMotorClient(host=host, port=port)

    def get_database(self, db_name: str):
        return self.client[db_name]

    def close(self):
        self.client.close()


mongodb_manager = MongoDBManager(
    host=os.getenv("MONGO_HOST"), port=int(os.getenv("MONGO_PORT"))
)

# mongodb_manager.get_database(os.getenv("DB_NAME")).command("ping")