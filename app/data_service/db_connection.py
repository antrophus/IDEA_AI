import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

class MongoDBConnection:
    def __init__(self, uri=None):
        self.uri = uri or os.getenv("MONGO_URI")
        self.client = MongoClient(self.uri)

    def get_db(self, db_name: str):
        return self.client[db_name]

    def get_collection(self, db_name: str, col_name: str):
        return self.client[db_name][col_name] 