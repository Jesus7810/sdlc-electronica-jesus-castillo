from uart_driver.config import UartConfig
from uart_driver.parsers import MessageParser


class UartDevice:
    def __init__(
        self,
        config: UartConfig,
        parser: MessageParser,
    ) -> None:
        self.config = config
        self.parser = parser
        self.is_connected = False

    def connect(self) -> None:
        self.is_connected = True

    def disconnect(self) -> None:
        self.is_connected = False

    def read_and_parse(self, message: bytes | str) -> dict:
        if not self.is_connected:
            raise RuntimeError("El dispositivo no está conectado.")
        return self.parser.parse(message)