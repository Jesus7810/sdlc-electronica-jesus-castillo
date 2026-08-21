from typing import Literal

SensorType = Literal["temperature", "humidity"]
VALID_UNITS: dict[str, str] = {"temperature": "C", "humidity": "%"}


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
