from .BaseRepository import BaseRepository
from ..Models.LecturaSensor import LecturaSensor
from ..Models.Medicion import Medicion

class MedicionRepository(BaseRepository):
    @classmethod
    def collection_name(cls) -> str:
        return "Sensores"

    @staticmethod
    def _filter_for_id(identifier):
        nodo, timestamp = identifier
        return {"nodo": nodo, "timestamp": timestamp}

    @staticmethod
    def _to_model(document):
        if document is None:
            return None
        if "sensor" in document:
            return LecturaSensor(
                timestamp=document["timestamp"],
                fecha_hora=document["fecha_hora"],
                nodo=document["nodo"],
                sensor=document["sensor"],
                valor=document["valor"],
            )
        return Medicion(
            timestamp=document["timestamp"],
            fecha_iso=document["fecha_iso"],
            fecha_lectura=document["fecha_lectura"],
            nodo=document["nodo"],
            sensores=document["sensores"],
            fecha_guardado=document["fecha_guardado"],
        )

    def create(self, entity: Medicion):
        result = self.collection.insert_one(vars(entity))
        return result.inserted_id

    def find_by_id(self, identifier):
        document = self.collection.find_one(self._filter_for_id(identifier))
        return self._to_model(document)

    def find_by_nodo_timestamp(self, nodo, timestamp):
        return self.find_by_id((nodo, timestamp))

    def find_all(self):
        return [self._to_model(document) for document in self.collection.find()]

    def update(self, identifier, entity: Medicion):
        fields_to_update = vars(entity).copy()
        fields_to_update.pop("nodo")
        fields_to_update.pop("timestamp")
        result = self.collection.update_one(
            self._filter_for_id(identifier),
            {"$set": fields_to_update},
        )
        return result.modified_count

    def delete(self, identifier):
        result = self.collection.delete_one(self._filter_for_id(identifier))
        return result.deleted_count
