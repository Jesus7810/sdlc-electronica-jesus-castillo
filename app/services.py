from datetime import UTC, datetime
from typing import Protocol, cast

from sqlalchemy.exc import IntegrityError

from app.domain import (
    VALID_UNITS,
    AlertCondition,
    AlertSeverity,
    AlertStatus,
    Anomaly,
    DomainValidationError,
    OperationalMetrics,
    ReadingAggregate,
    ResourceConflictError,
    ResourceNotFoundError,
    SensorReadingStatistics,
    classify_anomaly,
    validate_sensor_configuration,
)
from app.models import AlertModel, ReadingModel, SensorModel


class SensorRepository(Protocol):
    def add(self, sensor: SensorModel) -> SensorModel: ...
    def list(self, include_inactive: bool = False) -> list[SensorModel]: ...
    def get_by_id(self, sensor_id: str) -> SensorModel | None: ...
    def update(
        self, sensor: SensorModel, changes: dict[str, object]
    ) -> SensorModel: ...


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
            is_active=True,
            deactivated_at=None,
        )
        try:
            return self._repo.add(sensor)
        except IntegrityError as error:
            raise ResourceConflictError(
                "El identificador del sensor ya existe"
            ) from error

    def list(self, include_inactive: bool = False) -> list[SensorModel]:
        return self._repo.list(include_inactive)

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

    def deactivate(self, sensor_id: str) -> SensorModel:
        sensor = self.get(sensor_id)
        if not sensor.is_active:
            return sensor
        return self._repo.update(
            sensor,
            {
                "is_active": False,
                "deactivated_at": datetime.now(UTC),
            },
        )

    def activate(self, sensor_id: str) -> SensorModel:
        sensor = self.get(sensor_id)
        if sensor.is_active:
            return sensor
        return self._repo.update(
            sensor,
            {
                "is_active": True,
                "deactivated_at": None,
            },
        )


class ReadingRepository(Protocol):
    def add(
        self,
        sensor_id: str,
        value: float,
        unit: str,
        timestamp: datetime,
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

    def statistics(
        self,
        sensor_id: str,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> ReadingAggregate: ...

class AlertRepository(Protocol):
    def open_or_update(
        self, reading: ReadingModel, anomaly: Anomaly
    ) -> AlertModel: ...

    def get_by_id(self, alert_id: int) -> AlertModel | None: ...

    def acknowledge(self, alert: AlertModel) -> AlertModel: ...

    def resolve(self, alert: AlertModel) -> AlertModel: ...

    def list(
        self,
        sensor_id: str | None,
        status: AlertStatus | None,
        condition: AlertCondition | None,
        severity: AlertSeverity | None,
        offset: int,
        limit: int,
    ) -> list[AlertModel]: ...


class OperationalRepository(Protocol):
    def ping(self) -> None: ...

    def metrics(self) -> OperationalMetrics: ...


class OperationalService:
    def __init__(self, repo: OperationalRepository) -> None:
        self._repo = repo

    def ready(self) -> None:
        self._repo.ping()

    def metrics(self) -> OperationalMetrics:
        return self._repo.metrics()


class AlertStrategy(Protocol):
    def handle_anomaly(
        self,
        reading: ReadingModel,
        anomaly: Anomaly,
    ) -> None: ...


class DatabaseAlertStrategy:
    def __init__(self, repo: AlertRepository) -> None:
        self._repo = repo

    def handle_anomaly(
        self,
        reading: ReadingModel,
        anomaly: Anomaly,
    ) -> None:
        self._repo.open_or_update(reading, anomaly)


class AlertService:
    def __init__(self, repo: AlertRepository) -> None:
        self._repo = repo

    def get(self, alert_id: int) -> AlertModel:
        alert = self._repo.get_by_id(alert_id)
        if alert is None:
            raise ResourceNotFoundError("Alerta no encontrada")
        return alert

    def acknowledge(self, alert_id: int) -> AlertModel:
        alert = self.get(alert_id)
        if alert.status != AlertStatus.OPEN.value:
            raise ResourceConflictError("La alerta no puede ser reconocida")
        return self._repo.acknowledge(alert)

    def resolve(self, alert_id: int) -> AlertModel:
        alert = self.get(alert_id)
        if alert.status == AlertStatus.RESOLVED.value:
            raise ResourceConflictError("La alerta ya está resuelta")
        return self._repo.resolve(alert)

    def list(
        self,
        sensor_id: str | None,
        status: AlertStatus | None,
        condition: AlertCondition | None,
        severity: AlertSeverity | None,
        offset: int,
        limit: int,
    ) -> list[AlertModel]:
        return self._repo.list(
            sensor_id,
            status,
            condition,
            severity,
            offset,
            limit,
        )


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
        if not sensor.is_active:
            raise ResourceConflictError("El sensor est\u00e1 inactivo")
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

    @staticmethod
    def _normalize_utc_timestamp(timestamp: datetime) -> datetime:
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise InvalidTimestampError("El timestamp debe incluir zona horaria")
        return timestamp.astimezone(UTC)

    def record(
        self,
        sensor_id: str,
        value: float,
        unit: str,
        timestamp: datetime | None = None,
    ) -> ReadingModel:
        sensor = self._validate_for_sensor(sensor_id, value, unit)

        effective_timestamp = self._normalize_utc_timestamp(
            timestamp or datetime.now(UTC)
        )
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
        anomaly = classify_anomaly(
            created.value,
            sensor.low_critical_threshold,
            sensor.low_warning_threshold,
            sensor.high_warning_threshold,
            sensor.high_critical_threshold,
        )
        if anomaly is not None:
            self._alert_strategy.handle_anomaly(created, anomaly)

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
        normalized_from, normalized_to = self._normalize_date_range(
            from_date,
            to_date,
        )
        return self._repo.list(
            sensor_id,
            offset,
            limit,
            normalized_from,
            normalized_to,
        )

    def statistics(
        self,
        sensor_id: str,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> SensorReadingStatistics:
        sensor = self.require_sensor(sensor_id)
        normalized_from, normalized_to = self._normalize_date_range(
            from_date,
            to_date,
        )
        aggregate = self._repo.statistics(
            sensor_id,
            normalized_from,
            normalized_to,
        )
        return SensorReadingStatistics(
            sensor_id=sensor.id,
            unit=sensor.unit,
            from_timestamp=normalized_from,
            to_timestamp=normalized_to,
            count=aggregate.count,
            min_value=aggregate.min_value,
            max_value=aggregate.max_value,
            average_value=aggregate.average_value,
        )

    def _normalize_date_range(
        self,
        from_date: datetime | None,
        to_date: datetime | None,
    ) -> tuple[datetime | None, datetime | None]:
        normalized_from = (
            self._normalize_utc_timestamp(from_date)
            if from_date is not None
            else None
        )
        normalized_to = (
            self._normalize_utc_timestamp(to_date) if to_date is not None else None
        )
        if normalized_from is not None and normalized_to is not None:
            if normalized_from > normalized_to:
                raise InvalidDateRangeError(
                    "El parámetro 'from' no puede ser posterior a 'to'"
                )
        return normalized_from, normalized_to


class InvalidDateRangeError(ValueError):
    """Indica un intervalo de consulta cronológicamente inválido."""


class InvalidTimestampError(ValueError):
    """Indica que un timestamp no incluye zona horaria."""


class ReadingConflictError(Exception):
    """Indica que una lectura viola una restricción del dominio."""
