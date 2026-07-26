from datetime import datetime

from semana2.dia5_evaluacion1.alert_manager import AlertManager
from semana2.dia5_evaluacion1.anomaly_detector import AnomalyDetector
from semana2.dia5_evaluacion1.sensor_reading import SensorReading
from semana2.dia5_evaluacion1.sensor_simulator import SensorSimulator


class MonitoringService:
    def __init__(
        self,
        detector: AnomalyDetector,
        alert_manager: AlertManager,
    ) -> None:
        self._detector = detector
        self._alert_manager = alert_manager

    def run(
        self,
        simulators: list[SensorSimulator],
        cycles: int,
        measured_at: datetime,
    ) -> list[SensorReading]:
        readings: list[SensorReading] = []

        for _ in range(cycles):
            for simulator in simulators:
                reading = simulator.generate(measured_at)
                readings.append(reading)

                if self._detector.is_anomaly(reading):
                    message = f"{reading.sensor_id}: {reading.value}"
                    self._alert_manager.send_alert(message)

        return readings