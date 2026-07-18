from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class SensorReading:
    sensor_id: str
    value: float


# S - Single Responsibility Principle
# Ejemplo mal diseñado:
# La misma clase lee y guarda la medición.
class BadSensorManager:
    def read_sensor(self) -> float:
        return 25.0

    def save_reading(self, value: float) -> None:
        print(f"Guardando: {value}")

# Ejemplo bien diseñado:
# Cada clase tiene una sola responsabilidad.
class SensorReader:
    def read_sensor(self) -> float:
        return 25.0


class DataLogger:
    def save_reading(self, value: float) -> None:
        print(f"Guardando: {value}")


# O - Open/Closed Principle
# Ejemplo mal diseñado:
# Debe modificarse cuando se agrega un tipo de alerta.
class BadAnomalyDetector:
    def __init__(self, alert_type: str, threshold: float) -> None:
        self._alert_type = alert_type
        self._threshold = threshold

    def check(self, reading: SensorReading) -> None:
        if reading.value > self._threshold:
            message = f"Anomalia en {reading.sensor_id}"

            if self._alert_type == "console":
                print(message)
            elif self._alert_type == "email":
                print(f"Email: {message}")


# Ejemplo bien diseñado:
# Se pueden agregar nuevas estrategias sin modificar AnomalyDetector.
class AlertStrategy(ABC):
    @abstractmethod
    def send(self, message: str) -> None:
        ...


class ConsoleAlert(AlertStrategy):
    def send(self, message: str) -> None:
        print(message)


class EmailAlert(AlertStrategy):
    def send(self, message: str) -> None:
        print(f"Email: {message}")


class AnomalyDetector:
    def __init__(self, alert: AlertStrategy, threshold: float) -> None:
        self._alert = alert
        self._threshold = threshold

    def check(self, reading: SensorReading) -> None:
        if reading.value > self._threshold:
            self._alert.send(f"Anomalia en {reading.sensor_id}")


# L - Liskov Substitution Principle


class BaseSensor(ABC):
    @abstractmethod
    def read(self) -> float:
        ...


# Ejemplo mal diseñado:
# Declara que es un BaseSensor, pero no puede entregar una lectura.
class BrokenSensor(BaseSensor):
    def read(self) -> float:
        raise RuntimeError("El sensor no puede entregar una lectura")


# Ejemplo bien diseñado:
# Ambas clases respetan el contrato de BaseSensor.
class TemperatureSensor(BaseSensor):
    def read(self) -> float:
        return 25.0


class HumiditySensor(BaseSensor):
    def read(self) -> float:
        return 60.0


def process_sensor(sensor: BaseSensor) -> float:
    return sensor.read()