from isp_dip import (
    DataProcessor,
    Display,
    InMemoryRepository,
    SensorReading,
    TemperatureSensor,
)


def test_temperature_sensor_returns_value() -> None:
    sensor = TemperatureSensor(25.5)
    result = sensor.read()
    assert result == 25.5


def test_temperature_sensor_can_be_calibrated() -> None:
    sensor = TemperatureSensor(25.5)
    sensor.calibrate()
    assert sensor._is_calibrated is True


def test_display_writes_value(capsys) -> None:
    display = Display()
    display.write(25.5)
    captured = capsys.readouterr()
    assert captured.out == "El valor es 25.5\n"


def test_repository_returns_none_when_sensor_does_not_exist() -> None:
    repository = InMemoryRepository()
    result = repository.get_latest("T1")
    assert result is None


def test_repository_saves_reading() -> None:
    repository = InMemoryRepository()
    reading = SensorReading(sensor_id="T1", value=25.5)
    repository.save(reading)
    assert repository.get_latest("T1") == reading


def test_repository_replaces_previous_reading() -> None:
    repository = InMemoryRepository()
    first_reading = SensorReading(sensor_id="T1", value=25.5)
    latest_reading = SensorReading(sensor_id="T1", value=27.0)
    repository.save(first_reading)
    repository.save(latest_reading)
    assert repository.get_latest("T1") == latest_reading


def test_data_processor_processes_and_recovers_reading() -> None:
    repository = InMemoryRepository()
    processor = DataProcessor(repository)
    reading = SensorReading(sensor_id="T1", value=25.5)
    processor.process(reading)
    assert processor.get_latest("T1") == reading