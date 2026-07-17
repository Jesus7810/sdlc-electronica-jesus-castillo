from enum import Enum, auto
from dataclasses import dataclass
from typing import Protocol

class SensorType(Enum):
    TEMPERATURE = auto()
    HUMIDITY = auto()

@dataclass(frozen=True)
class Reading:
    sensor_id: str
    value: float
    sensor_type: SensorType

class Transport(Protocol):
    def send(self, payload: bytes) -> None:
        ...