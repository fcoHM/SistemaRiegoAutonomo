import board
import digitalio


class _ActuadorGPIO:
    def __init__(self, pin, activo_bajo=False):
        self.activo_bajo = activo_bajo
        self._salida = digitalio.DigitalInOut(pin)
        try:
            self._salida.direction = digitalio.Direction.OUTPUT
            self._salida.value = self.activo_bajo
        except Exception:
            self._salida.deinit()
            raise

    def encender(self):
        self._salida.value = not self.activo_bajo

    def apagar(self):
        self._salida.value = self.activo_bajo

    def cerrar(self):
        try:
            self.apagar()
        finally:
            self._salida.deinit()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.cerrar()


class BombaAgua(_ActuadorGPIO):
    """Controla la bomba conectada al GPIO BCM 15."""

    def __init__(self, activo_bajo=False):
        super().__init__(board.D15, activo_bajo)


class Electrovalvula(_ActuadorGPIO):
    """Controla la electroválvula conectada al GPIO BCM 13."""

    def __init__(self, activo_bajo=False):
        super().__init__(board.D13, activo_bajo)