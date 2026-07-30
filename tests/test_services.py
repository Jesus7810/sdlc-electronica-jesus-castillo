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
        timestamp: datetime | None = None,
    ) -> ReadingModel:
        reading = ReadingModel(
            id=len(self._readings) + 1,
            sensor_id=sensor_id,
            value=value,
            unit=unit,
            timestamp=timestamp or datetime.now(),
        )
        self._readings.append(reading)
        return reading

    def list(
        self,
        sensor_id: str | None,
        offset: int,
        limit: int,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> list[ReadingModel]:
        readings = self._readings

        if sensor_id is not None:
            readings = [
                reading for reading in readings if reading.sensor_id == sensor_id
            ]

        if from_date is not None:
            readings = [
                reading for reading in readings
                if reading.timestamp >= from_date
            ]
        if to_date is not None:
            readings = [
                reading for reading in readings
                if reading.timestamp <= to_date
            ]

        return readings[offset : offset + limit]

    def exists_at(self, sensor_id: str, timestamp: datetime) -> bool:
        return any(
            reading.sensor_id == sensor_id
            and reading.timestamp == timestamp
            for reading in self._readings
        )

    def get_by_id(self, reading_id: int) -> ReadingModel | None:
        return next(
            (reading for reading in self._readings if reading.id == reading_id),
            None,
        )

    def update(
        self,
        reading_id: int,
        value: float | None,
        unit: str | None,
    ) -> ReadingModel | None:
        reading = self.get_by_id(reading_id)

        if reading is None:
            return None

        if value is not None:
            reading.value = value

        if unit is not None:
            reading.unit = unit

        return reading

    def delete(self, reading_id: int) -> bool:
        reading = self.get_by_id(reading_id)

        if reading is None:
            return False

        self._readings.remove(reading)
        return True


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


def test_get_returns_existing_reading() -> None:
    repo: ReadingRepository = FakeReadingRepository()
    service = ReadingService(repo)

    created = service.record("TEMP-01", 25.5, "C")

    reading = service.get(created.id)

    assert reading == created


def test_get_returns_none_when_reading_does_not_exist() -> None:
    repo: ReadingRepository = FakeReadingRepository()
    service = ReadingService(repo)

    reading = service.get(999)

    assert reading is None


def test_update_changes_only_provided_fields() -> None:
    repo: ReadingRepository = FakeReadingRepository()
    service = ReadingService(repo)
    created = service.record("TEMP-01", 25.5, "C")

    updated = service.update(
        reading_id=created.id,
        value=30.0,
        unit=None,
    )

    assert updated is not None
    assert updated.value == 30.0
    assert updated.unit == "C"


def test_update_returns_none_when_reading_does_not_exist() -> None:
    repo: ReadingRepository = FakeReadingRepository()
    service = ReadingService(repo)

    updated = service.update(
        reading_id=999,
        value=30.0,
        unit=None,
    )

    assert updated is None


def test_update_rejects_temperature_below_absolute_zero() -> None:
    repo: ReadingRepository = FakeReadingRepository()
    service = ReadingService(repo)
    created = service.record("TEMP-01", 25.5, "C")

    with pytest.raises(
        ValueError,
        match="Temperatura por debajo del cero absoluto",
    ):
        service.update(
            reading_id=created.id,
            value=-274.0,
            unit=None,
        )


def test_delete_removes_existing_reading() -> None:
    repo: ReadingRepository = FakeReadingRepository()
    service = ReadingService(repo)
    created = service.record("TEMP-01", 25.5, "C")

    deleted = service.delete(created.id)

    assert deleted is True
    assert service.get(created.id) is None


def test_delete_returns_false_when_reading_does_not_exist() -> None:
    repo: ReadingRepository = FakeReadingRepository()
    service = ReadingService(repo)

    deleted = service.delete(999)

    assert deleted is False


def test_list_returns_paginated_readings() -> None:
    repo: ReadingRepository = FakeReadingRepository()
    service = ReadingService(repo)

    service.record("TEMP-01", 20.0, "C")
    second = service.record("HUM-01", 50.0, "%")
    third = service.record("TEMP-01", 21.0, "C")

    readings = service.list(
        sensor_id=None,
        offset=1,
        limit=2,
    )

    assert readings == [second, third]


def test_list_rejects_inverted_date_range() -> None:
    service = ReadingService(FakeReadingRepository())

    with pytest.raises(ValueError, match="'from'.*posterior"):
        service.list(
            sensor_id="TEMP-01",
            offset=0,
            limit=50,
            from_date=datetime(2026, 2, 1),
            to_date=datetime(2026, 1, 1),
        )
