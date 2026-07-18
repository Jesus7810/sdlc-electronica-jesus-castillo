# Driver UART modernizado

## Descripción

Este proyecto representa la modernización de un driver UART que originalmente
tenía variables globales, funciones de parsing separadas y responsabilidades
mezcladas.

La nueva versión divide el sistema en clases pequeñas:

- `UartConfig`: almacena y valida la configuración UART.
- `MessageParser`: define el comportamiento común de los parsers.
- `ModbusParser`: procesa frames Modbus simplificados.
- `NMEAParser`: procesa sentencias NMEA GPGGA.
- `UartDevice`: administra la conexión y utiliza un parser.
- `DataRecorder`: guarda los resultados en formato JSON Lines.

La comunicación UART se simula para poder probar el código sin utilizar
hardware real.

## Instalación

Instalar las herramientas necesarias:

```bash
pip install pytest ruff