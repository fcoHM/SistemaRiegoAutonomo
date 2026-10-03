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
import time
from typing import Dict, List, Optional, Tuple

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
    estado_bomba: bool = False,
) -> None:
    """Muestra la tabla de sensores con su ultima lectura y estado."""
    bomba_str = " BOMBA: [ACTIVA] " if estado_bomba else " BOMBA: [inactiva]"
    print(f"\n{'SENSOR':<26} {'LECTURA':>10}  ESTADO            {bomba_str}")
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
        self._estado_bomba: bool = False  # True = bomba activa

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
        en_marcha = bool(self._hilo_monitoreo and self._hilo_monitoreo.is_alive())
        estado_sistema = "[EN MARCHA]" if en_marcha else "[DETENIDO] "
        print(f"  Estado del sistema : {estado_sistema}")
        _imprimir_sensores(
            self._sensores_registrados,
            self._ultimas_lecturas,
            self._estado_bomba,
        )
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

        # Si el sistema no está corriendo, leer en vivo desde el sensor
        if not (self._hilo_monitoreo and self._hilo_monitoreo.is_alive()):
            with self._lock_lecturas:
                for nombre, sensor in self._sensores_registrados.items():
                    try:
                        self._ultimas_lecturas[nombre] = sensor.leer()
                    except Exception as exc:
                        print(f"  [!] Error leyendo '{nombre}': {exc}")

        _imprimir_sensores(
            self._sensores_registrados,
            self._ultimas_lecturas,
            self._estado_bomba,
        )
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
            # Ya está corriendo → entrar al dashboard directamente
            self._modo_dashboard()
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
        # Entrar al dashboard auto-refrescante
        self._modo_dashboard()

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

    def _modo_dashboard(self) -> None:
        """
        Pantalla auto-refrescante mientras el sistema de riego esta en marcha.
        Se actualiza cada vez que el Procesador completa un ciclo de monitoreo
        (evento_lectura) o como maximo cada segundo.
        Presionar cualquier tecla regresa al menu principal.
        """
        try:
            import msvcrt  # Windows
            def _keypress() -> bool:
                return msvcrt.kbhit()
            def _flush_key():
                while msvcrt.kbhit():
                    msvcrt.getch()
        except ImportError:
            # Fallback Unix: sin deteccion de tecla, salir con Ctrl+C
            _keypress = lambda: False
            _flush_key = lambda: None

        _flush_key()
        while self._hilo_monitoreo and self._hilo_monitoreo.is_alive():
            _limpiar_pantalla()
            _encabezado()
            print("  [SISTEMA EN MARCHA]  Presione cualquier tecla para volver al menu...")
            with self._lock_lecturas:
                _imprimir_sensores(
                    self._sensores_registrados,
                    self._ultimas_lecturas,
                    self._estado_bomba,
                )

            # Esperar señal del procesador o timeout de 1 s chequeando teclas
            inicio = time.monotonic()
            while time.monotonic() - inicio < 1.0:
                if _keypress():
                    _flush_key()
                    return
                # Salir del bucle interno si llegó evento de nueva lectura
                if self._procesador.evento_lectura.wait(timeout=0.05):
                    break

        # El hilo terminó: mostrar estado final
        _limpiar_pantalla()
        _encabezado()
        print("  [SISTEMA DETENIDO]")
        with self._lock_lecturas:
            _imprimir_sensores(
                self._sensores_registrados,
                self._ultimas_lecturas,
                self._estado_bomba,
            )
        input("\nPresione ENTER para volver al menu...")

    def _ejecutar_procesador(self, nombre_nodo: str) -> None:
        """Corre el procesador en un hilo separado y actualiza lecturas."""
        procesador = self._procesador
        vista = self

        # Guardamos el metodo original
        original_registrar = procesador._registrar_lecturas

        def _registrar_y_capturar():
            """Envuelve _registrar_lecturas para capturar las lecturas en la vista."""
            # Guardamos referencias antes de que el procesador haga la lectura
            humedad_seca = procesador.configuracion_actual["humedad_seca"]

            # Llamar al metodo original (que ya guarda en BD y activa bomba)
            original_registrar()

            # Leer de nuevo para actualizar la vista (1 lectura extra por ciclo)
            nuevas: Dict[str, Optional[float]] = {}
            necesita_riego = False
            with procesador._lock_sensores:
                sensores_snap = list(procesador._sensores.items())
            for nombre, sensor in sensores_snap:
                try:
                    val = sensor.leer()
                    nuevas[nombre] = val
                    if val < humedad_seca:
                        necesita_riego = True
                except Exception:
                    pass

            with vista._lock_lecturas:
                vista._ultimas_lecturas.update(nuevas)
                vista._estado_bomba = necesita_riego

        try:
            procesador._registrar_lecturas = _registrar_y_capturar
            procesador.iniciar(nombre_nodo=nombre_nodo)
        except Exception as exc:
            print(f"\n[ERROR] Error en el procesador: {exc}")
        finally:
            procesador._registrar_lecturas = original_registrar
            vista._estado_bomba = False

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
