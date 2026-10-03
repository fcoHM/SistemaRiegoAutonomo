"""Representa la medicion de un nodo con las lecturas de todos sus sensores."""


class Medicion:
    def __init__(
        self,
        timestamp,
        fecha_iso,
        fecha_lectura,
        nodo,
        sensores,
        fecha_guardado,
    ):
        self.timestamp = timestamp
        self.fecha_iso = fecha_iso
        self.fecha_lectura = fecha_lectura
        self.nodo = nodo
        self.sensores = sensores
        self.fecha_guardado = fecha_guardado