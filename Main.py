def main():
    from Controller.Procesador import Procesador
    from Model.Respositorys.ConfiguracionRepository import ConfiguracionRepository
    from Model.Respositorys.MedicionRepository import MedicionRepository
    from View.ConsolaView import ConsolaView

    repositorios = []
    procesador = None
    bomba = None
    bus_i2c = None

    try:
        configuracion_repository = ConfiguracionRepository()
        repositorios.append(configuracion_repository)
        medicion_repository = MedicionRepository()
        repositorios.append(medicion_repository)

        # Intentar inicializar hardware real (Raspberry Pi)
        # Si no hay hardware disponible, el sistema corre en modo simulado.
        try:
            import board
            from Controller.Sensores.ADS115 import ADS1115Device
            from Controller.Sensores.SensorHumedad import SensorHumedad
            from Controller.Sensores.ControladorActuadores import BombaAgua

            bus_i2c = board.I2C()
            ads1115 = ADS1115Device(bus_i2c)
            bomba = BombaAgua()

            def fabrica_sensor_real(nombre):
                # Registra el siguiente canal disponible (0-3)
                numero_canal = len(
                    [s for s in procesador._sensores]
                )
                canal = ads1115.registrar_canal(numero_canal)
                return SensorHumedad(canal, nombre)

            fabrica_sensor = fabrica_sensor_real
        except Exception:
            # Sin hardware: la ConsolaView usará sensores simulados
            fabrica_sensor = None

        procesador = Procesador(
            configuracion_repository,
            medicion_repository,
            bomba=bomba,
        )

        vista = ConsolaView(procesador, fabrica_sensor=fabrica_sensor)
        vista.ejecutar()

    except KeyboardInterrupt:
        print("\nDeteniendo el sistema de riego.")
    finally:
        if procesador is not None:
            procesador.detener()
        if bomba is not None:
            try:
                bomba.cerrar()
            except Exception:
                pass
        if bus_i2c is not None:
            try:
                bus_i2c.deinit()
            except Exception:
                pass
        for repositorio in repositorios:
            repositorio.close()


if __name__ == "__main__":
    main()
