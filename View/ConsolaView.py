"""
ConsolaView
===========
Interfaz de usuario basada en consola/terminal para el Sistema de Riego
Autónomo.  Permite:
  - Agregar sensores de humedad (máximo 4).
  - Iniciar el ciclo de monitoreo.
  - Ver la última lectura de cada sensor con su estado de humedad.

Estados de humedad (basados en el porcentaje 0-100 %):
  >= 70 %  -> "humeda"
  45-69 %  -> "parcialmente humeda"
  20-44 %  -> "semi seca"
  <  20 %  -> "seca"
"""

from __future__ import annotations

import os
import threading
from typing import Dict, Optional, Tuple

# ──────────────────────────────────────────────────────────────────────────────
# Constantes de estado
# ──────────────────────────────────────────────────────────────────────────────

MAX_SENSORES = 4

# Umbrales (límite inferior inclusivo de cada estado)
_RANGOS_ESTADO: Tuple[Tuple[float, str], ...] = (
    (70.0, "humeda"),
    (45.0, "parcialmente humeda"),
    (20.0, "semi seca"),
    (0.0,  "seca"),
)


def clasificar_humedad(porcentaje: float) -> str:
    """Devuelve el estado de humedad segun el porcentaje recibido (0-100)."""
    for umbral, estado in _RANGOS_ESTADO:
        if porcentaje >= umbral:
            return estado
    return "seca"


# ──────────────────────────────────────────────────────────────────────────────
# Helpers de presentación
# ──────────────────────────────────────────────────────────────────────────────

_SEP = "-" * 52


def _limpiar_pantalla() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def _encabezado() -> None:
    print(_SEP)
    print("   SISTEMA DE RIEGO AUTONOMO – CONSOLA")
    print(_SEP)


def _imprimir_sensores(
    sensores_registrados: Dict[str, object],
    ultimas_lecturas: Dict[str, Optional[float]],
) -> None:
    """Muestra la tabla de sensores con su ultima lectura y estado."""
    print(f"\n{'SENSOR':<26} {'LECTURA':>10}  ESTADO")
    print(_SEP)
    if not sensores_registrados:
        print("  (sin sensores registrados)")
    else:
        for nombre in sensores_registrados:
            lectura = ultimas_lecturas.get(nombre)
            if lectura is None:
                lectura_str = "  --.- %"
                estado_str  = "sin datos"
            else:
                lectura_str = f"{lectura:6.1f} %"
                estado_str  = clasificar_humedad(lectura)
            print(f"  {nombre:<24} {lectura_str:>10}  {estado_str}")

    slots_libres = MAX_SENSORES - len(sensores_registrados)
    print(f"\n  Slots disponibles: {slots_libres}/{MAX_SENSORES}")
    print(_SEP)


# ──────────────────────────────────────────────────────────────────────────────
# Clase principal
# ──────────────────────────────────────────────────────────────────────────────

class ConsolaView:
    """
    Interfaz de consola que orquesta la interaccion del usuario con el
    Procesador y los sensores de humedad.

    Parametros
    ----------
    procesador : Procesador
        Instancia del controlador principal del sistema.
    fabrica_sensor : callable, opcional
        Funcion ``fabrica_sensor(nombre) -> sensor`` usada para crear un
        sensor real cuando el usuario registra uno.  Si se omite, se crea
        un sensor simulado (util para pruebas sin hardware).
    """

    def __init__(self, procesador, fabrica_sensor=None):
        self._procesador = procesador
        self._fabrica_sensor = fabrica_sensor or self._sensor_simulado
        self._sensores_registrados: Dict[str, object] = {}
        self._ultimas_lecturas: Dict[str, Optional[float]] = {}
        self._lock_lecturas = threading.Lock()
        self._hilo_monitoreo: Optional[threading.Thread] = None

    # ── Interfaz pública ──────────────────────────────────────────────────────

    def ejecutar(self) -> None:
        """Bucle principal de la interfaz de consola."""
        _limpiar_pantalla()
        _encabezado()
        print("\nBienvenido al Sistema de Riego Autonomo.")

        while True:
            self._mostrar_menu_principal()
            opcion = input("Seleccione una opcion: ").strip()

            if opcion == "1":
                self._menu_agregar_sensor()
            elif opcion == "2":
                self._menu_ver_sensores()
            elif opcion == "3":
                self._menu_iniciar_sistema()
            elif opcion == "4":
                self._menu_detener_sistema()
            elif opcion == "5":
                self._salir()
                break
            else:
                print("\n[!] Opcion no valida. Intente de nuevo.")
                input("Presione ENTER para continuar...")

    # ── Menús ─────────────────────────────────────────────────────────────────

    def _mostrar_menu_principal(self) -> None:
        _limpiar_pantalla()
        _encabezado()
        _imprimir_sensores(self._sensores_registrados, self._ultimas_lecturas)
        print()
        print("  1. Agregar sensor de humedad")
        print("  2. Ver lecturas de sensores")
        print("  3. Iniciar sistema de riego")
        print("  4. Detener sistema de riego")
        print("  5. Salir")
        print()

    def _menu_agregar_sensor(self) -> None:
        _limpiar_pantalla()
        _encabezado()
        print("\n-- Agregar Sensor de Humedad --\n")

        if len(self._sensores_registrados) >= MAX_SENSORES:
            print(f"[!] Ya se han registrado el maximo de {MAX_SENSORES} sensores.")
            input("\nPresione ENTER para volver...")
            return

        nombre = input("Nombre del sensor (ej. sensor_zona_a): ").strip()
        if not nombre:
            print("[!] El nombre no puede estar vacio.")
            input("\nPresione ENTER para volver...")
            return

        if nombre in self._sensores_registrados:
            print(f"[!] Ya existe un sensor llamado '{nombre}'.")
            input("\nPresione ENTER para volver...")
            return

        try:
            sensor = self._fabrica_sensor(nombre)
            self._procesador.agregar_sensor(nombre, sensor)
            self._sensores_registrados[nombre] = sensor
            self._ultimas_lecturas[nombre] = None
            print(f"\n[OK] Sensor '{nombre}' registrado correctamente.")
        except (ValueError, TypeError) as exc:
            print(f"\n[ERROR] Error al registrar sensor: {exc}")

        input("\nPresione ENTER para volver...")

    def _menu_ver_sensores(self) -> None:
        _limpiar_pantalla()
        _encabezado()
        print("\n-- Lecturas Actuales de Sensores --\n")

        if not self._sensores_registrados:
            print("  (no hay sensores registrados)")
            input("\nPresione ENTER para volver...")
            return

        # Lectura en vivo: consulta cada sensor en el momento
        with self._lock_lecturas:
            for nombre, sensor in self._sensores_registrados.items():
                try:
                    valor = sensor.leer()
                    self._ultimas_lecturas[nombre] = valor
                except Exception as exc:
                    print(f"  [!] Error leyendo '{nombre}': {exc}")

        _imprimir_sensores(self._sensores_registrados, self._ultimas_lecturas)
        input("\nPresione ENTER para volver...")

    def _menu_iniciar_sistema(self) -> None:
        _limpiar_pantalla()
        _encabezado()
        print("\n-- Iniciar Sistema de Riego --\n")

        if not self._sensores_registrados:
            print("[!] Debe registrar al menos un sensor antes de iniciar.")
            input("\nPresione ENTER para volver...")
            return

        if self._hilo_monitoreo and self._hilo_monitoreo.is_alive():
            print("[i] El sistema ya esta en ejecucion.")
            input("\nPresione ENTER para volver...")
            return

        nombre_nodo = input("Nombre del nodo (ej. nodo_principal): ").strip()
        if not nombre_nodo:
            print("[!] El nombre del nodo no puede estar vacio.")
            input("\nPresione ENTER para volver...")
            return

        self._hilo_monitoreo = threading.Thread(
            target=self._ejecutar_procesador,
            args=(nombre_nodo,),
            daemon=True,
            name="hilo-procesador",
        )
        self._hilo_monitoreo.start()
        print(f"\n[OK] Sistema iniciado en nodo '{nombre_nodo}'.")
        input("\nPresione ENTER para volver al menu...")

    def _menu_detener_sistema(self) -> None:
        _limpiar_pantalla()
        _encabezado()
        print("\n-- Detener Sistema de Riego --\n")

        if not (self._hilo_monitoreo and self._hilo_monitoreo.is_alive()):
            print("[i] El sistema no esta en ejecucion actualmente.")
        else:
            self._procesador.detener()
            self._hilo_monitoreo.join(timeout=5)
            print("[OK] Sistema detenido correctamente.")

        input("\nPresione ENTER para volver...")

    def _salir(self) -> None:
        _limpiar_pantalla()
        _encabezado()
        print("\nDeteniendo el sistema...")
        self._procesador.detener()
        if self._hilo_monitoreo and self._hilo_monitoreo.is_alive():
            self._hilo_monitoreo.join(timeout=5)
        print("Hasta luego!\n")

    # ── Internos ─────────────────────────────────────────────────────────────

    def _ejecutar_procesador(self, nombre_nodo: str) -> None:
        """Corre el procesador en un hilo separado y actualiza lecturas."""
        # Guardamos el método original para poder restaurarlo
        procesador_original_registrar = self._procesador._registrar_lecturas
        vista = self  # captura para el closure

        def _registrar_y_actualizar():
            procesador_original_registrar()
            # Refrescar últimas lecturas para la vista
            with vista._lock_lecturas:
                for nombre, sensor in vista._sensores_registrados.items():
                    try:
                        vista._ultimas_lecturas[nombre] = sensor.leer()
                    except Exception:
                        pass

        try:
            self._procesador._registrar_lecturas = _registrar_y_actualizar
            self._procesador.iniciar(nombre_nodo=nombre_nodo)
        except Exception as exc:
            print(f"\n[ERROR] Error en el procesador: {exc}")
        finally:
            # Restaurar el método original
            self._procesador._registrar_lecturas = procesador_original_registrar

    @staticmethod
    def _sensor_simulado(nombre: str):
        """
        Crea un sensor simulado que devuelve valores aleatorios.
        Util para demostracion sin hardware fisico.
        """
        import random

        class _SensorSimulado:
            def __init__(self, nombre_sensor: str):
                self.nombre = nombre_sensor

            def leer(self) -> float:
                return round(random.uniform(0.0, 100.0), 1)

        return _SensorSimulado(nombre)
