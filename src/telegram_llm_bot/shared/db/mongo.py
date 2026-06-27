import logging
import os

from motor.motor_asyncio import AsyncIOMotorClient

from telegram_llm_bot.paths import load_environment

load_environment()

logger = logging.getLogger(__name__)


class MongoDBManager:
    def __init__(self, host, port):
        self.client = AsyncIOMotorClient(host=host, port=port)

    def get_database(self, db_name: str):
        return self.client[db_name]

    def close(self):
        self.client.close()

    async def ping(self):
        await self.client.admin.command("ping")


class LazyMongoDBManager:
    def __init__(self):
        self.manager = None

    def _get_manager(self):
        if self.manager is None:
            host = os.getenv("MONGO_HOST")
            port = os.getenv("MONGO_PORT")
            if not host or not port:
                raise ValueError("Set MONGO_HOST and MONGO_PORT to use MongoDB")
            self.manager = MongoDBManager(host=host, port=int(port))
        return self.manager

    def get_database(self, db_name: str):
        return self._get_manager().get_database(db_name)

    def close(self):
        if self.manager is not None:
            self.manager.close()

    async def ping(self):
        await self._get_manager().ping()


mongodb_manager = LazyMongoDBManager()
