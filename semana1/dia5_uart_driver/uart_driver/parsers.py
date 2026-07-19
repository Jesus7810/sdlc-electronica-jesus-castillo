from abc import ABC, abstractmethod


class MessageParser(ABC):
    """Define las operaciones que debe tener cualquier parser."""

    @abstractmethod
    def can_parse(self, message: bytes | str) -> bool:
        """Indica si el mensaje puede ser procesado."""

    @abstractmethod
    def parse(self, message: bytes | str) -> dict:
        """Convierte el mensaje en un diccionario."""


class ModbusParser(MessageParser):
    """Procesa frames Modbus RTU simplificados."""

    def can_parse(self, message: bytes | str) -> bool:
        return isinstance(message, bytes) and len(message) >= 3

    def parse(self, message: bytes | str) -> dict:
        if not self.can_parse(message):
            raise ValueError("Frame Modbus inválido.")

        if not isinstance(message, bytes):
            raise TypeError("El mensaje Modbus debe ser de tipo bytes.")

        return {
            "protocol": "modbus",
            "address": message[0],
            "function": message[1],
            "data": list(message[2:]),
        }


class NMEAParser(MessageParser):
    """Procesa sentencias NMEA de tipo GPGGA."""

    def can_parse(self, message: bytes | str) -> bool:
        return isinstance(message, str) and message.startswith("$GPGGA,")

    def parse(self, message: bytes | str) -> dict:
        if not self.can_parse(message):
            raise ValueError("Sentencia NMEA inválida.")

        if not isinstance(message, str):
            raise TypeError("El mensaje NMEA debe ser texto.")

        fields = message.split(",")

        return {
            "protocol": "nmea",
            "time": fields[1],
            "latitude": fields[2],
            "longitude": fields[4],
        }