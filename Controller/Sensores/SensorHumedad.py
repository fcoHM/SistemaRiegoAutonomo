# este es la represntancion del sensor de humedad
import time

class SensorHumedad:
    MUESTRAS = 10
    VALOR_SECO = 25000
    VALOR_MOJADO = 12000

    def __init__(self, canal, nombre_sensor = ""):
        self.canal = canal
        self.nombre = nombre_sensor

    def leer_promedio(self):
        suma = 0
        for _ in range(self.MUESTRAS):
            suma += self.canal.leer_valor()
            time.sleep(0.01)
        promedio = suma // self.MUESTRAS
        return promedio

    def calcular_porcentaje(self, valor):
        rango = self.VALOR_SECO - self.VALOR_MOJADO
        porcentaje = ((self.VALOR_SECO - valor) / rango) * 100
        return float(max(0.0, min(100.0, porcentaje)))

    def leer(self):
        valor = self.leer_promedio()
        return self.calcular_porcentaje(valor)
