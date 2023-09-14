import os

from motor.motor_asyncio import AsyncIOMotorClient


class MongoDBManager:
    def __init__(self, host, port):
        self.client = AsyncIOMotorClient(host=host, port=port)

    def get_database(self, db_name):
        return self.client[db_name]

    def close(self):
        self.client.close()


mongodb_manager = MongoDBManager(
    host=os.getenv("MONGO_HOST"), port=int(os.getenv("MONGO_PORT"))
)
