import pytest

from solid import (
    AnomalyDetector,
    BadAnomalyDetector,
    BadSensorManager,
    BrokenSensor,
    ConsoleAlert,
    DataLogger,
    HumiditySensor,
    SensorReader,
    SensorReading,
    TemperatureSensor,
    process_sensor,
)


# Tests de SRP
def test_bad_sensor_manager_has_two_responsibilities(capsys) -> None:
    manager = BadSensorManager()

    value = manager.read_sensor()
    manager.save_reading(value)

    captured = capsys.readouterr()

    assert value == 25.0
    assert captured.out == "Guardando: 25.0\n"


def test_sensor_reader_and_data_logger_work_separately(capsys) -> None:
    reader = SensorReader()
    logger = DataLogger()

    value = reader.read_sensor()
    logger.save_reading(value)

    captured = capsys.readouterr()

    assert value == 25.0
    assert captured.out == "Guardando: 25.0\n"


# Tests de OCP
def test_bad_anomaly_detector_uses_alert_type(capsys) -> None:
    detector = BadAnomalyDetector(
        alert_type="console",
        threshold=30.0,
    )
    reading = SensorReading(sensor_id="T1", value=35.0)

    detector.check(reading)

    captured = capsys.readouterr()

    assert captured.out == "Anomalia en T1\n"


def test_anomaly_detector_uses_alert_strategy(capsys) -> None:
    alert = ConsoleAlert()
    detector = AnomalyDetector(
        alert=alert,
        threshold=30.0,
    )
    reading = SensorReading(sensor_id="T1", value=35.0)

    detector.check(reading)

    captured = capsys.readouterr()

    assert captured.out == "Anomalia en T1\n"


# Tests de LSP=
def test_broken_sensor_cannot_replace_base_sensor() -> None:
    sensor = BrokenSensor()

    with pytest.raises(RuntimeError):
        process_sensor(sensor)


def test_temperature_and_humidity_sensors_are_interchangeable() -> None:
    temperature_sensor = TemperatureSensor()
    humidity_sensor = HumiditySensor()

    assert process_sensor(temperature_sensor) == 25.0
    assert process_sensor(humidity_sensor) == 60.0