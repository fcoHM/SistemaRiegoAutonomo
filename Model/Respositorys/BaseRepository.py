from abc import ABC, abstractmethod
from .DBClient import DBClient

# este es la base de todos los repositorios
class BaseRepository(ABC):
    def __init__(self):
        self.db_client = DBClient()
        self.data_base_in_use = self.db_client.database
        self.collection = self.db_client.get_collection(self.collection_name())


    @classmethod
    @abstractmethod
    def collection_name(cls) -> str:
        pass

    @abstractmethod
    def create(self, entity):
        pass

    @abstractmethod
    def find_by_id(self, identifier):
        pass

    @abstractmethod
    def find_all(self):
        pass

    @abstractmethod
    def update(self, identifier, entity):
        pass

    @abstractmethod
    def delete(self, identifier):
        pass
    
