from datetime import UTC, datetime

import pytest

from semana2.dia5_evaluacion1.anomaly_detector import AnomalyDetector
from semana2.dia5_evaluacion1.sensor_reading import MeasurementType, SensorReading


def create_reading(
    measurement_type: MeasurementType,
    value: float,
) -> SensorReading:
    return SensorReading(
        sensor_id="SENSOR-01",
        measurement_type=measurement_type,
        value=value,
        measured_at=datetime.now(UTC),
    )


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (34.9, False),
        (35.0, False),
        (35.1, True),
    ],
)
def test_detect_temperature_anomaly(value: float, expected: bool) -> None:
    detector = AnomalyDetector(
        temperature_threshold=35.0,
        humidity_threshold=80.0,
    )
    reading = create_reading(MeasurementType.TEMPERATURE, value)

    assert detector.is_anomaly(reading) is expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (79.9, False),
        (80.0, False),
        (80.1, True),
    ],
)
def test_detect_humidity_anomaly(value: float, expected: bool) -> None:
    detector = AnomalyDetector(
        temperature_threshold=35.0,
        humidity_threshold=80.0,
    )
    reading = create_reading(MeasurementType.HUMIDITY, value)

    assert detector.is_anomaly(reading) is expected


def test_use_injected_thresholds() -> None:
    detector = AnomalyDetector(
        temperature_threshold=30.0,
        humidity_threshold=70.0,
    )

    temperature = create_reading(MeasurementType.TEMPERATURE, 31.0)
    humidity = create_reading(MeasurementType.HUMIDITY, 71.0)

    assert detector.is_anomaly(temperature) is True
    assert detector.is_anomaly(humidity) is True


@pytest.mark.parametrize(
    ("temperature_threshold", "humidity_threshold"),
    [
        (float("inf"), 80.0),
        (float("-inf"), 80.0),
        (float("nan"), 80.0),
        (35.0, float("inf")),
        (35.0, float("-inf")),
        (35.0, float("nan")),
    ],
)
def test_reject_non_finite_thresholds(
    temperature_threshold: float,
    humidity_threshold: float,
) -> None:
    with pytest.raises(ValueError, match="los umbrales deben ser finitos"):
        AnomalyDetector(
            temperature_threshold=temperature_threshold,
            humidity_threshold=humidity_threshold,
        )