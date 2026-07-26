import math
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class MeasurementType(Enum):
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"


@dataclass(frozen=True)
class SensorReading:
    sensor_id: str
    measurement_type: MeasurementType
    value: float
    measured_at: datetime

    def __post_init__(self) -> None:
        if not self.sensor_id.strip():
            raise ValueError("sensor_id no puede estar vacío")

        if not math.isfinite(self.value):
            raise ValueError("value debe ser finito")

        if self.measured_at.tzinfo is None:
            raise ValueError("measured_at debe incluir zona horaria")