from dataclasses import FrozenInstanceError
from uart_driver.config import UartConfig
import pytest


def test_create_valid_config() -> None:
    """Debe crear una configuración válida."""
    config = UartConfig(baudrate=9600)
    assert config.baudrate == 9600
    assert config.parity == "N"


def test_invalid_baudrate() -> None:
    """Debe rechazar un baudrate inválido."""
    with pytest.raises(ValueError):
        UartConfig(baudrate=0)


def test_config_is_immutable() -> None:
    """No debe permitir modificar la configuración."""
    config = UartConfig(baudrate=9600)
    with pytest.raises(FrozenInstanceError):
        config.baudrate = 115200  # type: ignore[misc]