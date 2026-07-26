from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from semana2.dia5_evaluacion1.sensor_reading import MeasurementType, SensorReading


def test_create_valid_sensor_reading() -> None:
    measured_at = datetime(2026, 7, 25, 12, 0, tzinfo=UTC)

    reading = SensorReading(
        sensor_id="TEMP-01",
        measurement_type=MeasurementType.TEMPERATURE,
        value=24.5,
        measured_at=measured_at,
    )

    assert reading.sensor_id == "TEMP-01"
    assert reading.measurement_type is MeasurementType.TEMPERATURE
    assert reading.value == 24.5
    assert reading.measured_at == measured_at


def test_reject_empty_sensor_id() -> None:
    with pytest.raises(ValueError, match="sensor_id no puede estar vacío"):
        SensorReading(
            sensor_id="  ",
            measurement_type=MeasurementType.HUMIDITY,
            value=60.0,
            measured_at=datetime.now(UTC),
        )


@pytest.mark.parametrize("value", [float("inf"), float("-inf"), float("nan")])
def test_reject_non_finite_value(value: float) -> None:
    with pytest.raises(ValueError, match="value debe ser finito"):
        SensorReading(
            sensor_id="TEMP-01",
            measurement_type=MeasurementType.TEMPERATURE,
            value=value,
            measured_at=datetime.now(UTC),
        )


def test_reject_timestamp_without_timezone() -> None:
    with pytest.raises(ValueError, match="measured_at debe incluir zona horaria"):
        SensorReading(
            sensor_id="TEMP-01",
            measurement_type=MeasurementType.TEMPERATURE,
            value=24.5,
            measured_at=datetime(2026, 7, 25, 12, 0),
        )


def test_sensor_reading_is_immutable() -> None:
    reading = SensorReading(
        sensor_id="TEMP-01",
        measurement_type=MeasurementType.TEMPERATURE,
        value=24.5,
        measured_at=datetime.now(UTC),
    )

    with pytest.raises(FrozenInstanceError):
        reading.value = 40.0  # type: ignore[misc]