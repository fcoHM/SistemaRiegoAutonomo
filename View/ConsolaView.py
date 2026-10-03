"""Panel de consola de una sola pantalla para el sistema de riego."""

from __future__ import annotations

import os
import threading
from typing import Dict, Optional, Tuple

MAX_SENSORES = 4

_RANGOS_ESTADO: Tuple[Tuple[float, str], ...] = (
    (70.0, "humeda"),
    (45.0, "parcialmente humeda"),
    (20.0, "semi seca"),
    (0.0, "seca"),
)


def clasificar_humedad(porcentaje: float) -> str:
    """Devuelve el estado de humedad segun el porcentaje recibido (0-100)."""
    for umbral, estado in _RANGOS_ESTADO:
        if porcentaje >= umbral:
            return estado
    return "seca"


def _limpiar_pantalla() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def _encabezado() -> None:
    print("-" * 68)
    print("   SISTEMA DE RIEGO AUTONOMO")
    print("-" * 68)


def _imprimir_sensores(
    sensores_registrados: Dict[str, object],
    ultimas_lecturas: Dict[str, Optional[float]],
    estado_bomba: bool = False,
) -> None:
    bomba = "riego requerido" if estado_bomba else "sin riego"
    print(f"\n{'SENSOR':<28} {'LECTURA':>10}  {'ESTADO':<24} {bomba}")
    print("-" * 68)
    if not sensores_registrados:
        print("  (sin sensores registrados)")
    else:
        for nombre in sensores_registrados:
            lectura = ultimas_lecturas.get(nombre)
            if lectura is None:
                lectura_str = "--.- %"
                estado_str = "sin datos"
            else:
                lectura_str = f"{lectura:6.1f} %"
                estado_str = clasificar_humedad(lectura)
            print(f"  {nombre:<26} {lectura_str:>10}  {estado_str}")

    libres = MAX_SENSORES - len(sensores_registrados)
    print(f"\n  Sensores disponibles: {libres}/{MAX_SENSORES}")
    print("-" * 68)


class ConsolaView:
    """Muestra sensores, lecturas y controles en un panel persistente."""

    def __init__(self, procesador, fabrica_sensor=None):
        self._procesador = procesador
        self._fabrica_sensor = fabrica_sensor or self._sensor_simulado
        self._sensores_registrados: Dict[str, object] = {}
        self._ultimas_lecturas: Dict[str, Optional[float]] = {}
        self._hilo_monitoreo: Optional[threading.Thread] = None
        self._estado_bomba = False
        self._mensaje = ""

    def ejecutar(self) -> None:
        """Mantiene el panel abierto y lo redibuja solo ante cambios."""
        version = self._procesador.version_cambios
        estado = self._estado_interfaz()
        self._actualizar_lecturas()
        self._mostrar_panel()

        while True:
            tecla = self._leer_tecla()
            if tecla:
                if self._procesar_tecla(tecla):
                    return
                version = self._procesador.version_cambios
                estado = self._estado_interfaz()
                self._actualizar_lecturas()
                self._mostrar_panel()
                continue

            nueva_version = self._procesador.esperar_cambio(version, timeout=0.05)
            nuevo_estado = self._estado_interfaz()
            if nueva_version != version or nuevo_estado != estado:
                version = nueva_version
                estado = nuevo_estado
                self._actualizar_lecturas()
                self._mostrar_panel()

    def _mostrar_panel(self) -> None:
        _limpiar_pantalla()
        _encabezado()
        en_marcha = bool(self._hilo_monitoreo and self._hilo_monitoreo.is_alive())
        print(f"  Estado del sistema: {'EN MARCHA' if en_marcha else 'DETENIDO'}")
        _imprimir_sensores(
            self._sensores_registrados,
            self._ultimas_lecturas,
            self._estado_bomba,
        )
        print("  [1] Agregar sensor   [2] Iniciar monitoreo")
        print("  [3] Detener monitoreo   [4] Salir")
        if self._mensaje:
            print(f"\n  {self._mensaje}")
        print("\n  Seleccione una opcion:")

    def _estado_interfaz(self):
        hilo_activo = bool(self._hilo_monitoreo and self._hilo_monitoreo.is_alive())
        return hilo_activo, self._mensaje

    @staticmethod
    def _leer_tecla() -> str:
        try:
            import msvcrt

            if not msvcrt.kbhit():
                return ""
            tecla = msvcrt.getwch()
            return "" if tecla in ("\x00", "\xe0") else tecla
        except ImportError:
            import select
            import sys

            disponibles, _, _ = select.select([sys.stdin], [], [], 0)
            return sys.stdin.read(1) if disponibles else ""

    def _procesar_tecla(self, tecla: str) -> bool:
        tecla = tecla.lower()
        if tecla == "1":
            self._agregar_sensor()
        elif tecla == "2":
            self._iniciar_monitoreo()
        elif tecla == "3":
            self._detener_monitoreo()
        elif tecla == "4":
            self._salir()
            return True
        else:
            self._mensaje = "Opcion no valida. Use 1, 2, 3 o 4."
        return False

    def _agregar_sensor(self) -> None:
        if len(self._sensores_registrados) >= MAX_SENSORES:
            self._mensaje = f"Ya se registro el maximo de {MAX_SENSORES} sensores."
            return

        nombre = input("\nNombre del sensor (ej. sensor_zona_a): ").strip()
        if not nombre:
            self._mensaje = "El nombre del sensor no puede estar vacio."
            return
        if nombre in self._sensores_registrados:
            self._mensaje = f"Ya existe un sensor llamado '{nombre}'."
            return

        try:
            sensor = self._fabrica_sensor(nombre)
            self._procesador.agregar_sensor(nombre, sensor)
        except (ValueError, TypeError) as exc:
            self._mensaje = f"Error al registrar el sensor: {exc}"
            return

        self._sensores_registrados[nombre] = sensor
        self._ultimas_lecturas[nombre] = None
        self._mensaje = f"Sensor '{nombre}' registrado correctamente."

    def _iniciar_monitoreo(self) -> None:
        if not self._sensores_registrados:
            self._mensaje = "Registre al menos un sensor antes de iniciar."
            return
        if self._hilo_monitoreo and self._hilo_monitoreo.is_alive():
            self._mensaje = "El monitoreo ya esta en marcha."
            return

        nombre_nodo = input("\nNombre del nodo (ej. nodo_principal): ").strip()
        if not nombre_nodo:
            self._mensaje = "El nombre del nodo no puede estar vacio."
            return

        self._mensaje = "Iniciando monitoreo..."
        self._hilo_monitoreo = threading.Thread(
            target=self._ejecutar_procesador,
            args=(nombre_nodo,),
            daemon=True,
            name="hilo-procesador",
        )
        self._hilo_monitoreo.start()

    def _detener_monitoreo(self) -> None:
        if not self._hilo_monitoreo or not self._hilo_monitoreo.is_alive():
            self._mensaje = "El sistema no esta en ejecucion."
            return

        self._procesador.detener()
        self._hilo_monitoreo.join(timeout=5)
        self._mensaje = (
            "Monitoreo detenido."
            if not self._hilo_monitoreo.is_alive()
            else "El monitoreo sigue deteniendose."
        )

    def _salir(self) -> None:
        self._procesador.detener()
        if self._hilo_monitoreo and self._hilo_monitoreo.is_alive():
            self._hilo_monitoreo.join(timeout=5)
        print("\nHasta luego.")

    def _actualizar_lecturas(self) -> None:
        self._ultimas_lecturas.update(self._procesador.obtener_ultimas_lecturas())
        configuracion = self._procesador.configuracion_actual
        humedad_seca = configuracion.get("humedad_seca") if configuracion else None
        self._estado_bomba = bool(
            humedad_seca is not None
            and any(
                lectura is not None and lectura < humedad_seca
                for lectura in self._ultimas_lecturas.values()
            )
        )

    def _ejecutar_procesador(self, nombre_nodo: str) -> None:
        try:
            self._procesador.iniciar(nombre_nodo=nombre_nodo)
        except Exception as exc:
            self._mensaje = f"Error en el procesador: {exc}"

    @staticmethod
    def _sensor_simulado(nombre: str):
        """Crea un sensor simulado para ejecutar el sistema sin hardware."""
        import random

        class _SensorSimulado:
            def __init__(self, nombre_sensor: str):
                self.nombre = nombre_sensor

            def leer(self) -> float:
                return round(random.uniform(0.0, 100.0), 1)

        return _SensorSimulado(nombre)
