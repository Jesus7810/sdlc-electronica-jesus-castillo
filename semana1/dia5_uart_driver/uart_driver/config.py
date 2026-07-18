from dataclasses import dataclass


@dataclass(frozen=True)
class UartConfig:
    baudrate: int
    parity: str = "N"
    stop_bits: int = 1
    timeout: float = 1.0

    def __post_init__(self) -> None:
        if self.baudrate <= 0:
            raise ValueError("El baudrate debe ser mayor que cero.")

        if self.parity not in ("N", "E", "O"):
            raise ValueError("La paridad debe ser N, E u O.")

        if self.stop_bits not in (1, 2):
            raise ValueError("Los bits de parada deben ser 1 o 2.")

        if self.timeout < 0:
            raise ValueError("El timeout no puede ser negativo.")