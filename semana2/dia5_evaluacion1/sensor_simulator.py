import random
from datetime import datetime

from semana2.dia5_evaluacion1.sensor_reading import (
    MeasurementType,
    SensorReading,
)


class SensorSimulator:
    def __init__(
        self,
        sensor_id: str,
        measurement_type: MeasurementType,
        mean: float,
        standard_deviation: float,
        seed: int,
    ) -> None:
        if standard_deviation <= 0:
            raise ValueError("standard_deviation debe ser positiva")

        self._sensor_id = sensor_id
        self._measurement_type = measurement_type
        self._mean = mean
        self._standard_deviation = standard_deviation
        self._random = random.Random(seed)

    def generate(self, measured_at: datetime) -> SensorReading:
        value = self._random.gauss(
            self._mean,
            self._standard_deviation,
        )

        return SensorReading(
            sensor_id=self._sensor_id,
            measurement_type=self._measurement_type,
            value=value,
            measured_at=measured_at,
        )