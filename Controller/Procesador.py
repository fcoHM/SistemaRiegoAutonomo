from datetime import datetime, timezone
from math import isfinite
from numbers import Real
from threading import Event, Lock
from time import monotonic, time_ns

from Model.Models.LecturaSensor import LecturaSensor


class Procesador:
	MAX_SENSORES = 4
	CONFIGURACIONES_REQUERIDAS = (
		"humedad_mojado",
		"intervalo_configuracion",
		"tiempo_riego",
		"intervalo_monitoreo",
	)

	def __init__(
		self,
		configuracion_repository,
		medicion_repository,
		solicitar_nombre_nodo=None,
		reloj=None,
	):
		self.configuracion_repository = configuracion_repository
		self.medicion_repository = medicion_repository
		self.solicitar_nombre_nodo = solicitar_nombre_nodo
		self._reloj = reloj or monotonic
		self._detener = Event()
		self._lock_sensores = Lock()
		self._sensores = {}
		self.nombre_nodo = None
		self.configuracion_actual = None
		self._siguiente_actualizacion = None
		self._siguiente_monitoreo = None
		self._ejecutando = False

	def agregar_sensor(self, nombre, sensor):
		if not isinstance(nombre, str) or not nombre.strip():
			raise ValueError("El sensor debe tener un nombre no vacío.")
		if not callable(getattr(sensor, "leer", None)):
			raise TypeError("El sensor debe proporcionar un método leer().")

		nombre = nombre.strip()
		with self._lock_sensores:
			if nombre in self._sensores:
				raise ValueError(f"Ya existe un sensor llamado {nombre}.")
			if len(self._sensores) >= self.MAX_SENSORES:
				raise ValueError("No se pueden registrar más de 4 sensores.")
			self._sensores[nombre] = sensor

	def detener(self):
		self._detener.set()

	def iniciar(self, nombre_nodo=None):
		if self._ejecutando:
			raise RuntimeError("El procesador ya está en ejecución.")

		with self._lock_sensores:
			if not 1 <= len(self._sensores) <= self.MAX_SENSORES:
				raise ValueError("Se requiere registrar entre 1 y 4 sensores antes de iniciar.")

		if nombre_nodo is None:
			solicitar = self.solicitar_nombre_nodo or input
			nombre_nodo = solicitar("Nombre del nodo: ")
		if not isinstance(nombre_nodo, str) or not nombre_nodo.strip():
			raise ValueError("El nombre del nodo no puede estar vacío.")

		self.nombre_nodo = nombre_nodo.strip()
		self.configuracion_actual = self._obtener_configuracion()
		ahora = self._reloj()
		self._siguiente_actualizacion = ahora + self._minutos_a_segundos(
			self.configuracion_actual["intervalo_configuracion"]
		)
		self._siguiente_monitoreo = ahora
		self._detener.clear()
		self._ejecutando = True

		try:
			while not self._detener.is_set():
				espera = self.procesar_pendientes()
				self._detener.wait(espera)
		finally:
			self._ejecutando = False

	def procesar_pendientes(self):
		if self.configuracion_actual is None:
			raise RuntimeError("El procesador debe inicializarse antes de procesar.")

		ahora = self._reloj()
		if ahora >= self._siguiente_actualizacion:
			self.configuracion_actual = self._obtener_configuracion()
			ahora = self._reloj()
			self._siguiente_actualizacion = ahora + self._minutos_a_segundos(
				self.configuracion_actual["intervalo_configuracion"]
			)

		if ahora >= self._siguiente_monitoreo:
			self._registrar_lecturas()
			ahora = self._reloj()
			self._siguiente_monitoreo = ahora + self._minutos_a_segundos(
				self.configuracion_actual["intervalo_monitoreo"]
			)

		return max(
			0.0,
			min(self._siguiente_actualizacion, self._siguiente_monitoreo) - self._reloj(),
		)

	def _obtener_configuracion(self):
		valores = {}
		for nombre in self.CONFIGURACIONES_REQUERIDAS:
			entidad = self.configuracion_repository.find_by_nodo_objeto(
				self.nombre_nodo, nombre
			)
			if entidad is None:
				raise ValueError(f"Falta la configuración '{nombre}' para el nodo.")
			valores[nombre] = entidad.value

		self._validar_numero("humedad_mojado", valores["humedad_mojado"], 0, 100)
		self._validar_numero(
			"intervalo_configuracion",
			valores["intervalo_configuracion"],
			0,
			minimo_exclusivo=True,
		)
		self._validar_numero("tiempo_riego", valores["tiempo_riego"], 0)
		self._validar_numero(
			"intervalo_monitoreo",
			valores["intervalo_monitoreo"],
			0,
			minimo_exclusivo=True,
		)
		return valores

	@staticmethod
	def _validar_numero(nombre, valor, minimo, maximo=None, minimo_exclusivo=False):
		if isinstance(valor, bool) or not isinstance(valor, Real) or not isfinite(valor):
			raise ValueError(f"La configuración '{nombre}' debe ser un número válido.")
		limite_inferior_invalido = valor <= minimo if minimo_exclusivo else valor < minimo
		if limite_inferior_invalido or (maximo is not None and valor > maximo):
			if maximo is None:
				comparacion = "mayor que" if minimo_exclusivo else "mayor o igual a"
				raise ValueError(f"La configuración '{nombre}' debe ser {comparacion} {minimo}.")
			raise ValueError(f"La configuración '{nombre}' debe estar entre {minimo} y {maximo}.")

	@staticmethod
	def _minutos_a_segundos(minutos):
		return float(minutos) * 60

	def _registrar_lecturas(self):
		with self._lock_sensores:
			sensores = tuple(self._sensores.items())

		for nombre, sensor in sensores:
			valor = sensor.leer()
			self._validar_numero(f"lectura de {nombre}", valor, 0, 100)
			fecha_hora = datetime.now(timezone.utc)
			lectura = LecturaSensor(
				timestamp=time_ns(),
				fecha_hora=fecha_hora,
				nodo=self.nombre_nodo,
				sensor=nombre,
				valor=float(valor),
			)
			self.medicion_repository.create(lectura)
