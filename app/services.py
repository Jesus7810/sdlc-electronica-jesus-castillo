from datetime import UTC, datetime
from typing import Protocol, cast

from sqlalchemy.exc import IntegrityError

from app.domain import (
    VALID_UNITS,
    DomainValidationError,
    ResourceConflictError,
    ResourceNotFoundError,
    validate_sensor_configuration,
)
from app.models import AlertModel, ReadingModel, SensorModel


class SensorRepository(Protocol):
    def add(self, sensor: SensorModel) -> SensorModel: ...
    def list(self) -> list[SensorModel]: ...
    def get_by_id(self, sensor_id: str) -> SensorModel | None: ...
    def update(
        self, sensor: SensorModel, changes: dict[str, object]
    ) -> SensorModel: ...
    def delete(self, sensor: SensorModel) -> None: ...


class SensorService:
    def __init__(
        self,
        repo: SensorRepository,
        reading_repo: "ReadingRepository",
    ) -> None:
        self._repo = repo
        self._reading_repo = reading_repo

    def create(
        self,
        sensor_id: str,
        name: str,
        location: str,
        sensor_type: str,
        unit: str,
        min_value: float,
        low_critical_threshold: float,
        low_warning_threshold: float,
        high_warning_threshold: float,
        high_critical_threshold: float,
        max_value: float,
    ) -> SensorModel:
        validate_sensor_configuration(
            sensor_type,
            unit,
            min_value,
            low_critical_threshold,
            low_warning_threshold,
            high_warning_threshold,
            high_critical_threshold,
            max_value,
        )
        if self._repo.get_by_id(sensor_id) is not None:
            raise ResourceConflictError("El identificador del sensor ya existe")
        sensor = SensorModel(
            id=sensor_id,
            name=name,
            location=location,
            type=sensor_type,
            unit=unit,
            min_value=min_value,
            low_critical_threshold=low_critical_threshold,
            low_warning_threshold=low_warning_threshold,
            high_warning_threshold=high_warning_threshold,
            high_critical_threshold=high_critical_threshold,
            max_value=max_value,
        )
        try:
            return self._repo.add(sensor)
        except IntegrityError as error:
            raise ResourceConflictError(
                "El identificador del sensor ya existe"
            ) from error

    def list(self) -> list[SensorModel]:
        return self._repo.list()

    def get(self, sensor_id: str) -> SensorModel:
        sensor = self._repo.get_by_id(sensor_id)
        if sensor is None:
            raise ResourceNotFoundError("Sensor no encontrado")
        return sensor

    def update(
        self,
        sensor_id: str,
        changes: dict[str, object],
    ) -> SensorModel:
        sensor = self.get(sensor_id)
        sensor_type = cast(str, changes.get("type", sensor.type))
        unit = cast(str, changes.get("unit", sensor.unit))
        min_value = cast(float, changes.get("min_value", sensor.min_value))
        low_critical_threshold = cast(
            float,
            changes.get("low_critical_threshold", sensor.low_critical_threshold),
        )
        low_warning_threshold = cast(
            float,
            changes.get("low_warning_threshold", sensor.low_warning_threshold),
        )
        high_warning_threshold = cast(
            float,
            changes.get("high_warning_threshold", sensor.high_warning_threshold),
        )
        high_critical_threshold = cast(
            float,
            changes.get("high_critical_threshold", sensor.high_critical_threshold),
        )
        max_value = cast(float, changes.get("max_value", sensor.max_value))
        validate_sensor_configuration(
            sensor_type,
            unit,
            min_value,
            low_critical_threshold,
            low_warning_threshold,
            high_warning_threshold,
            high_critical_threshold,
            max_value,
        )
        has_readings = self._reading_repo.has_for_sensor(sensor_id)
        type_changed = sensor_type != sensor.type
        unit_changed = unit != sensor.unit
        if has_readings and (type_changed or unit_changed):
            raise ResourceConflictError(
                "No se puede cambiar tipo o unidad con lecturas existentes"
            )
        if has_readings and not self._reading_repo.all_within_range(
            sensor_id, min_value, max_value
        ):
            raise ResourceConflictError("El nuevo rango excluye lecturas existentes")
        return self._repo.update(sensor, changes)

    def delete(self, sensor_id: str) -> None:
        self._repo.delete(self.get(sensor_id))


class ReadingRepository(Protocol):
    def add(
        self,
        sensor_id: str,
        value: float,
        unit: str,
        timestamp: datetime | None = None,
    ) -> ReadingModel: ...

    def exists_at(self, sensor_id: str, timestamp: datetime) -> bool: ...
    def has_for_sensor(self, sensor_id: str) -> bool: ...
    def all_within_range(
        self, sensor_id: str, min_value: float, max_value: float
    ) -> bool: ...

    def list(
        self,
        sensor_id: str | None,
        offset: int,
        limit: int,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> list[ReadingModel]: ...

    def get_by_id(
        self,
        reading_id: int,
    ) -> ReadingModel | None: ...

    def update(
        self,
        reading_id: int,
        value: float | None,
        unit: str | None,
    ) -> ReadingModel | None: ...

    def delete(self, reading_id: int) -> bool: ...


class AlertRepository(Protocol):
    def add(
        self,
        sensor_id: str,
        reading_id: int,
        reading_value: float,
        threshold: float,
    ) -> AlertModel: ...

    def list(self) -> list[AlertModel]: ...


class AlertStrategy(Protocol):
    def handle_anomaly(
        self,
        reading: ReadingModel,
        threshold: float,
    ) -> None: ...


class DatabaseAlertStrategy:
    def __init__(self, repo: AlertRepository) -> None:
        self._repo = repo

    def handle_anomaly(
        self,
        reading: ReadingModel,
        threshold: float,
    ) -> None:
        self._repo.add(
            reading.sensor_id,
            reading.id,
            reading.value,
            threshold,
        )


class AlertService:
    def __init__(self, repo: AlertRepository) -> None:
        self._repo = repo

    def list(self) -> list[AlertModel]:
        return self._repo.list()


class ReadingService:
    """Contiene la lógica de negocio de las lecturas."""

    def __init__(
        self,
        repo: ReadingRepository,
        sensor_repo: SensorRepository,
        alert_strategy: AlertStrategy,
    ) -> None:
        self._repo = repo
        self._sensor_repo = sensor_repo
        self._alert_strategy = alert_strategy

    def require_sensor(self, sensor_id: str) -> SensorModel:
        sensor = self._sensor_repo.get_by_id(sensor_id)
        if sensor is None:
            raise ResourceNotFoundError("Sensor no encontrado")
        return sensor

    def _validate_for_sensor(
        self,
        sensor_id: str,
        value: float,
        unit: str,
    ) -> SensorModel:
        sensor = self.require_sensor(sensor_id)
        if sensor.type == "temperature" and value < -273.15:
            raise ValueError("Temperatura por debajo del cero absoluto")
        if unit != sensor.unit or VALID_UNITS[sensor.type] != unit:
            raise DomainValidationError(
                "La unidad de la lectura no coincide con el sensor"
            )
        if not sensor.min_value <= value <= sensor.max_value:
            raise DomainValidationError(
                "El valor está fuera del rango operativo del sensor"
            )
        return sensor

    def record(
        self,
        sensor_id: str,
        value: float,
        unit: str,
        timestamp: datetime | None = None,
    ) -> ReadingModel:
        sensor = self._validate_for_sensor(sensor_id, value, unit)

        effective_timestamp = timestamp or datetime.now(UTC).replace(tzinfo=None)
        if self._repo.exists_at(sensor_id, effective_timestamp):
            raise ReadingConflictError(
                "Ya existe una lectura para este sensor en esa fecha"
            )
        try:
            created = self._repo.add(
                sensor_id,
                value,
                unit,
                effective_timestamp,
            )
        except IntegrityError as error:
            raise ReadingConflictError(
                "Ya existe una lectura para este sensor en esa fecha"
            ) from error
        if created.value > sensor.high_warning_threshold:
            self._alert_strategy.handle_anomaly(
                created,
                sensor.high_warning_threshold,
            )

        return created

    def get(self, reading_id: int) -> ReadingModel | None:
        return self._repo.get_by_id(reading_id)

    def list(
        self,
        sensor_id: str | None,
        offset: int,
        limit: int,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> list[ReadingModel]:
        if from_date is not None and to_date is not None:
            from_is_naive = from_date.tzinfo is None
            to_is_naive = to_date.tzinfo is None
            if from_is_naive != to_is_naive:
                raise InvalidDateRangeError(
                    "Los parámetros 'from' y 'to' deben usar la misma zona horaria"
                )
            if from_date > to_date:
                raise InvalidDateRangeError(
                    "El parámetro 'from' no puede ser posterior a 'to'"
                )
        return self._repo.list(
            sensor_id,
            offset,
            limit,
            from_date,
            to_date,
        )

    def update(
        self,
        reading_id: int,
        value: float | None,
        unit: str | None,
    ) -> ReadingModel | None:
        reading = self._repo.get_by_id(reading_id)
        if reading is None:
            return None
        effective_value = value if value is not None else reading.value
        effective_unit = unit if unit is not None else reading.unit
        self._validate_for_sensor(
            reading.sensor_id,
            effective_value,
            effective_unit,
        )
        return self._repo.update(reading_id, value, unit)

    def delete(self, reading_id: int) -> bool:
        return self._repo.delete(reading_id)


class InvalidDateRangeError(ValueError):
    """Indica un intervalo de consulta cronológicamente inválido."""


class ReadingConflictError(Exception):
    """Indica que una lectura viola una restricción del dominio."""
