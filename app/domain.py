from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

SensorType = Literal["temperature", "humidity"]
VALID_UNITS: dict[str, str] = {"temperature": "C", "humidity": "%"}


class AlertCondition(StrEnum):
    LOW = "low"
    HIGH = "high"


class AlertSeverity(StrEnum):
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AlertStatus(StrEnum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


@dataclass(frozen=True)
class Anomaly:
    condition: AlertCondition
    severity: AlertSeverity
    threshold: float


def classify_anomaly(
    value: float,
    low_critical_threshold: float,
    low_warning_threshold: float,
    high_warning_threshold: float,
    high_critical_threshold: float,
) -> Anomaly | None:
    if value <= low_critical_threshold:
        return Anomaly(
            AlertCondition.LOW,
            AlertSeverity.CRITICAL,
            low_critical_threshold,
        )
    if value < low_warning_threshold:
        return Anomaly(
            AlertCondition.LOW,
            AlertSeverity.WARNING,
            low_warning_threshold,
        )
    if value >= high_critical_threshold:
        return Anomaly(
            AlertCondition.HIGH,
            AlertSeverity.CRITICAL,
            high_critical_threshold,
        )
    if value > high_warning_threshold:
        return Anomaly(
            AlertCondition.HIGH,
            AlertSeverity.WARNING,
            high_warning_threshold,
        )
    return None


def validate_sensor_configuration(
    sensor_type: str,
    unit: str,
    min_value: float,
    low_critical_threshold: float,
    low_warning_threshold: float,
    high_warning_threshold: float,
    high_critical_threshold: float,
    max_value: float,
) -> None:
    if not (
        min_value
        < low_critical_threshold
        < low_warning_threshold
        < high_warning_threshold
        < high_critical_threshold
        < max_value
    ):
        raise DomainValidationError(
            "Los lÃ­mites fÃ­sicos y umbrales deben mantener un orden estricto"
        )
    if VALID_UNITS.get(sensor_type) != unit:
        raise DomainValidationError("El tipo y la unidad no son compatibles")


class DomainValidationError(ValueError):
    """Indica que una operación viola una regla física del dominio."""


class ResourceNotFoundError(Exception):
    """Indica que una entidad solicitada no existe."""


class ResourceConflictError(Exception):
    """Indica un conflicto con el estado persistido."""
