from datetime import datetime

import pytest

from app.models import ReadingModel
from app.services import ReadingRepository, ReadingService


class FakeReadingRepository:
    def __init__(self) -> None:
        self._readings: list[ReadingModel] = []

    def add(
        self,
        sensor_id: str,
        value: float,
        unit: str,
    ) -> ReadingModel:
        reading = ReadingModel(
            id=len(self._readings) + 1,
            sensor_id=sensor_id,
            value=value,
            unit=unit,
            timestamp=datetime.now(),
        )
        self._readings.append(reading)
        return reading

    def list_for_sensor(self, sensor_id: str) -> list[ReadingModel]:
        return [
            reading
            for reading in self._readings
            if reading.sensor_id == sensor_id
        ]


def test_record_saves_valid_reading() -> None:
    repo: ReadingRepository = FakeReadingRepository()
    service = ReadingService(repo)

    reading = service.record("TEMP-01", 25.5, "C")

    assert reading.sensor_id == "TEMP-01"
    assert reading.value == 25.5
    assert reading.unit == "C"


def test_record_rejects_temperature_below_absolute_zero() -> None:
    repo: ReadingRepository = FakeReadingRepository()
    service = ReadingService(repo)

    with pytest.raises(
        ValueError,
        match="Temperatura por debajo del cero absoluto",
    ):
        service.record("TEMP-01", -274.0, "C")


def test_record_accepts_exact_absolute_zero() -> None:
    repo: ReadingRepository = FakeReadingRepository()
    service = ReadingService(repo)

    reading = service.record("TEMP-01", -273.15, "C")

    assert reading.value == -273.15