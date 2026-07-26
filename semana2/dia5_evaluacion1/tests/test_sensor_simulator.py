from datetime import UTC, datetime

import pytest

from semana2.dia5_evaluacion1.sensor_reading import MeasurementType
from semana2.dia5_evaluacion1.sensor_simulator import SensorSimulator


def test_generate_reproducible_sequence_with_same_seed() -> None:
    first_simulator = SensorSimulator(
        sensor_id="TEMP-01",
        measurement_type=MeasurementType.TEMPERATURE,
        mean=25.0,
        standard_deviation=2.0,
        seed=42,
    )
    second_simulator = SensorSimulator(
        sensor_id="TEMP-01",
        measurement_type=MeasurementType.TEMPERATURE,
        mean=25.0,
        standard_deviation=2.0,
        seed=42,
    )
    measured_at = datetime(2026, 7, 25, 12, 0, tzinfo=UTC)

    first_values = [
        first_simulator.generate(measured_at).value
        for _ in range(5)
    ]
    second_values = [
        second_simulator.generate(measured_at).value
        for _ in range(5)
    ]

    assert first_values == second_values


def test_generate_sensor_reading_with_configured_data() -> None:
    simulator = SensorSimulator(
        sensor_id="HUM-01",
        measurement_type=MeasurementType.HUMIDITY,
        mean=60.0,
        standard_deviation=5.0,
        seed=10,
    )
    measured_at = datetime(2026, 7, 25, 12, 0, tzinfo=UTC)

    reading = simulator.generate(measured_at)

    assert reading.sensor_id == "HUM-01"
    assert reading.measurement_type is MeasurementType.HUMIDITY
    assert reading.measured_at == measured_at


@pytest.mark.parametrize("standard_deviation", [0.0, -1.0])
def test_reject_non_positive_standard_deviation(
    standard_deviation: float,
) -> None:
    with pytest.raises(
        ValueError,
        match="standard_deviation debe ser positiva",
    ):
        SensorSimulator(
            sensor_id="TEMP-01",
            measurement_type=MeasurementType.TEMPERATURE,
            mean=25.0,
            standard_deviation=standard_deviation,
            seed=42,
        )