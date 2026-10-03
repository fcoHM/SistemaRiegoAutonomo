import adafruit_ads1x15.ads1115 as ADS
from .Canal import Canal

class ADS1115Device:
    """
    Representa el conversor analógico-digital ADS1115 físico conectado vía I2C.
    """
    DIRECCIONES_VALIDAS = {0x48, 0x49, 0x4A, 0x4B}

    def __init__(self, i2c, address=0x48):
        if i2c is None:
            raise ValueError("Se requiere un bus I2C válido para el dispositivo ADS1115.")
        if address not in self.DIRECCIONES_VALIDAS:
            raise ValueError("La dirección del ADS1115 debe estar entre 0x48 y 0x4B.")

        self.address = address
        self.canales = {}
        self.ads = ADS.ADS1115(i2c, address=address)

    def registrar_canal(self, numero_canal):
        """
        Registra y retorna un canal del ADS1115 si todavía no está en uso.
        """
        if numero_canal in self.canales:
            raise ValueError(f"El canal {numero_canal} ya está en uso")

        canal = Canal(self.ads, numero_canal)
        self.canales[numero_canal] = canal
        return canal
