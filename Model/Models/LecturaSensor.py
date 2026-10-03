class LecturaSensor:
    """Representa una lectura de humedad de un sensor de un nodo."""

    def __init__(self, timestamp, fecha_hora, nodo, sensor, valor):
        self.timestamp = timestamp
        self.fecha_hora = fecha_hora
        self.nodo = nodo
        self.sensor = sensor
        self.valor = valor