from .BaseRepository import BaseRepository
from ..Models.Configuracion import Configuracion


class ConfiguracionRepository(BaseRepository):

    @classmethod
    def collection_name(cls) -> str:
        return "Configuracion"

    
    @staticmethod
    def _filter_for_id(identifier):
        nodo, objeto = identifier
        return {"nodo": nodo, "object": objeto}

    @staticmethod # convertir en documento
    def _to_model(document):
        if document is None:
            return None
        return Configuracion(
            nodo=document["nodo"],
            object=document["object"],
            value=document["value"],
        )

    def create(self, entity: Configuracion):
        result = self.collection.insert_one(vars(entity))
        return result.inserted_id

    def find_by_id(self, identifier):
        document = self.collection.find_one(self._filter_for_id(identifier))
        return self._to_model(document)

    def find_by_nodo_objeto(self, nodo, objeto):
        return self.find_by_id((nodo, objeto))

    def find_all(self):
        return [self._to_model(document) for document in self.collection.find()]

    def update(self, identifier, entity: Configuracion):
        result = self.collection.update_one(
            self._filter_for_id(identifier),
            {"$set": vars(entity)},
        )
        return result.modified_count

    def delete(self, identifier):
        result = self.collection.delete_one(self._filter_for_id(identifier))
        return result.deleted_count
        