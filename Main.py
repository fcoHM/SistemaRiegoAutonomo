SENSORES = (("sensor_humedad_1", 0),)


def main():
	from Controller.Procesador import Procesador
	from Controller.Sensores.ADS115 import ADS1115Device
	from Controller.Sensores.SensorHumedad import SensorHumedad
	from Model.Respositorys.ConfiguracionRepository import ConfiguracionRepository
	from Model.Respositorys.MedicionRepository import MedicionRepository
	import board

	repositorios = []
	bus_i2c = None
	procesador = None

	try:
		configuracion_repository = ConfiguracionRepository()
		repositorios.append(configuracion_repository)
		medicion_repository = MedicionRepository()
		repositorios.append(medicion_repository)

		bus_i2c = board.I2C()
		ads1115 = ADS1115Device(bus_i2c)
		procesador = Procesador(configuracion_repository, medicion_repository)

		for nombre, numero_canal in SENSORES:
			canal = ads1115.registrar_canal(numero_canal)
			procesador.agregar_sensor(nombre, SensorHumedad(canal, nombre))

		procesador.iniciar()
	except KeyboardInterrupt:
		print("\nDeteniendo el sistema de riego.")
	finally:
		if procesador is not None:
			procesador.detener()
		if bus_i2c is not None:
			try:
				bus_i2c.deinit()
			finally:
				for repositorio in repositorios:
					repositorio.close()
		else:
			for repositorio in repositorios:
				repositorio.close()


if __name__ == "__main__":
	main()
