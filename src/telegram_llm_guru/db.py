import os

from pymongo import MongoClient


# TODO maybe switch to motor for async mongo
class MongoDBManager:
    def __init__(self, host, port):
        self.client = MongoClient(host, port)

    def get_database(self, db_name):
        return self.client[db_name]

    def close(self):
        self.client.close()


mongodb_manager = MongoDBManager(host=os.getenv("MONGO_HOST"), port=27017)
