from uart_driver.config import UartConfig
from uart_driver.device import UartDevice
from uart_driver.parsers import ModbusParser, NMEAParser
import pytest

def test_device_connects() -> None:
    """Debe cambiar su estado al conectarse."""
    config = UartConfig(baudrate=9600)
    device = UartDevice(config, ModbusParser())
    device.connect()
    assert device.is_connected is True


def test_device_disconnects() -> None:
    """Debe cambiar su estado al desconectarse."""
    config = UartConfig(baudrate=9600)
    device = UartDevice(config, ModbusParser())
    device.connect()
    device.disconnect()
    assert device.is_connected is False


def test_device_cannot_read_when_disconnected() -> None:
    """Debe impedir lecturas cuando no está conectado."""
    config = UartConfig(baudrate=9600)
    device = UartDevice(config, NMEAParser())
    with pytest.raises(RuntimeError):
        device.read_and_parse(
            "$GPGGA,123519,1907.000,N,09655.000,W"
        )