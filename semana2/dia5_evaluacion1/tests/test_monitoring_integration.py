from datetime import UTC, datetime

from semana2.dia5_evaluacion1.alert_manager import AlertManager
from semana2.dia5_evaluacion1.anomaly_detector import AnomalyDetector
from semana2.dia5_evaluacion1.monitoring_service import MonitoringService
from semana2.dia5_evaluacion1.sensor_reading import MeasurementType
from semana2.dia5_evaluacion1.sensor_simulator import SensorSimulator


class FakeAlertStrategy:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def send(self, message: str) -> None:
        self.messages.append(message)


def test_monitor_ten_sensors_during_sixty_cycles() -> None:
    simulators = [
        SensorSimulator(
            sensor_id=f"TEMP-{index}",
            measurement_type=MeasurementType.TEMPERATURE,
            mean=35.0,
            standard_deviation=2.0,
            seed=index,
        )
        for index in range(5)
    ]

    simulators.extend(
        SensorSimulator(
            sensor_id=f"HUM-{index}",
            measurement_type=MeasurementType.HUMIDITY,
            mean=80.0,
            standard_deviation=5.0,
            seed=index + 5,
        )
        for index in range(5)
    )

    strategy = FakeAlertStrategy()
    alert_manager = AlertManager(strategy)
    detector = AnomalyDetector(
        temperature_threshold=35.0,
        humidity_threshold=80.0,
    )
    service = MonitoringService(detector, alert_manager)

    readings = service.run(
        simulators=simulators,
        cycles=60,
        measured_at=datetime(2026, 7, 25, 12, 0, tzinfo=UTC),
    )

    anomalous_readings = [
        reading
        for reading in readings
        if detector.is_anomaly(reading)
    ]

    assert len(readings) == 600
    assert len(strategy.messages) == len(anomalous_readings)