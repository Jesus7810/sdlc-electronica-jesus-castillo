from typing import Protocol
from dataclasses import dataclass

# ISP
class Readable(Protocol):
    def read(self) -> float: ...


class Writable(Protocol):
    def write(self, value: float) -> None: ...


class Calibratable(Protocol):
    def calibrate(self) -> None: ...


class TemperatureSensor:
    def __init__(self, value: float) -> None:
        self._value = value
        self._is_calibrated = False
    
    def read(self) -> float:
        return self._value
    
    def calibrate(self) -> None:
        self._is_calibrated = True


class Display:
    def write(self, value: float) -> None:
        print(f"El valor es {value}")


# DIP
@dataclass(frozen=True)
class SensorReading:
    sensor_id: str
    value: float


class DataRepository(Protocol):
    def save(self, reading: SensorReading) -> None: ...
    def get_latest(self, sensor_id:str) -> SensorReading | None:...


class InMemoryRepository:
    def __init__(self) -> None:
        self._readings: dict[str, SensorReading] = {}

    def save(self, reading: SensorReading) -> None:
        self._readings[reading.sensor_id] = reading

    def get_latest(self, sensor_id: str) -> SensorReading | None:
        return self._readings.get(sensor_id)
        

class DataProcessor:
    def __init__(self, repository: DataRepository) -> None:
        self._repository = repository

    def process(self, reading: SensorReading) -> None:
        self._repository.save(reading)

    def get_latest(self, sensor_id: str) -> SensorReading | None:
        return self._repository.get_latest(sensor_id)    