from typing import Literal

SensorType = Literal["temperature", "humidity"]
VALID_UNITS: dict[str, str] = {"temperature": "C", "humidity": "%"}


def validate_sensor_configuration(
    sensor_type: str,
    unit: str,
    min_value: float,
    max_value: float,
) -> None:
    if min_value >= max_value:
        raise DomainValidationError("min_value debe ser menor que max_value")
    if VALID_UNITS.get(sensor_type) != unit:
        raise DomainValidationError("El tipo y la unidad no son compatibles")


class DomainValidationError(ValueError):
    """Indica que una operación viola una regla física del dominio."""


class ResourceNotFoundError(Exception):
    """Indica que una entidad solicitada no existe."""


class ResourceConflictError(Exception):
    """Indica un conflicto con el estado persistido."""
