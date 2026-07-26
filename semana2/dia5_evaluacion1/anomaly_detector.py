import math
from dataclasses import dataclass

from semana2.dia5_evaluacion1.sensor_reading import (
    MeasurementType,
    SensorReading,
)


@dataclass(frozen=True)
class AnomalyDetector:
    temperature_threshold: float
    humidity_threshold: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.temperature_threshold):
            raise ValueError("los umbrales deben ser finitos")

        if not math.isfinite(self.humidity_threshold):
            raise ValueError("los umbrales deben ser finitos")

    def is_anomaly(self, reading: SensorReading) -> bool:
        if reading.measurement_type is MeasurementType.TEMPERATURE:
            return reading.value > self.temperature_threshold

        return reading.value > self.humidity_threshold