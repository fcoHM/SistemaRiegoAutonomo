import os
from pathlib import Path

from dotenv import load_dotenv
from pymongo import MongoClient as PyMongoClient


class DBClient:
    def __init__(self, env_path=None):
        if env_path is None:
            env_path = Path(__file__).resolve().parents[2] / "atlas-credentials.env"

        load_dotenv(dotenv_path=env_path)

        uri = os.getenv("MONGODB_URI")
        username = os.getenv("MONGODB_USERNAME")
        password = os.getenv("MONGODB_PASSWORD")
        database_name = os.getenv("MONGODB_DATABASE")

        missing = [
            name
            for name, value in (
                ("MONGODB_URI", uri),
                ("MONGODB_USERNAME", username),
                ("MONGODB_PASSWORD", password),
                ("MONGODB_DATABASE", database_name),
            )
            if not value
        ]
        if missing:
            raise ValueError(f"Faltan variables de entorno: {', '.join(missing)}")

        self.client = PyMongoClient(uri, username=username, password=password)
        self.database = self.client[database_name]

    def get_collection(self, name: str):
        return self.database[name]

    def close(self):
        self.client.close()