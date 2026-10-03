from adafruit_ads1x15.analog_in import AnalogIn

class Canal:
    """
    Representa un canal físico del conversor analógico-digital ADS1115
    conectado a un pin específico para la lectura de un sensor.
    """
    def __init__(self, ads, numero):
        if ads is None:
            raise ValueError("Se requiere una instancia válida de ADS1115 para inicializar el canal.")
        if isinstance(numero, bool) or not isinstance(numero, int) or not 0 <= numero <= 3:
            raise ValueError("El número de canal debe ser un entero entre 0 y 3.")

        self.numero = numero
        self.analog = AnalogIn(ads, numero)

    def leer_valor(self):
        """
        Retorna el valor digital crudo leído del canal (rango 0 a 32767 para lecturas unipolares).
        """
        return self.analog.value

    def leer_voltaje(self):
        """
        Retorna el voltaje real leído en el canal físico.
        """
        return self.analog.voltage
