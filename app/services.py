from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy.exc import IntegrityError

from app.models import ReadingModel


class ReadingRepository(Protocol):
    def add(
        self,
        sensor_id: str,
        value: float,
        unit: str,
        timestamp: datetime | None = None,
    ) -> ReadingModel: ...

    def exists_at(self, sensor_id: str, timestamp: datetime) -> bool: ...

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


class ReadingService:
    """Contiene la lógica de negocio de las lecturas."""

    def __init__(self, repo: ReadingRepository) -> None:
        self._repo = repo

    def record(
        self,
        sensor_id: str,
        value: float,
        unit: str,
        timestamp: datetime | None = None,
    ) -> ReadingModel:
        if value < -273.15:
            raise ValueError(
                "Temperatura por debajo del cero absoluto"
            )

        effective_timestamp = timestamp or datetime.now(UTC).replace(tzinfo=None)
        if self._repo.exists_at(sensor_id, effective_timestamp):
            raise ReadingConflictError(
                "Ya existe una lectura para este sensor en esa fecha"
            )
        try:
            return self._repo.add(
                sensor_id,
                value,
                unit,
                effective_timestamp,
            )
        except IntegrityError as error:
            raise ReadingConflictError(
                "Ya existe una lectura para este sensor en esa fecha"
            ) from error

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
        if from_date is not None and to_date is not None and from_date > to_date:
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
        if value is not None and value < -273.15:
            raise ValueError(
                "Temperatura por debajo del cero absoluto"
            )

        return self._repo.update(reading_id, value, unit)

    def delete(self, reading_id: int) -> bool:
        return self._repo.delete(reading_id)


class InvalidDateRangeError(ValueError):
    """Indica un intervalo de consulta cronológicamente inválido."""


class ReadingConflictError(Exception):
    """Indica que una lectura viola una restricción del dominio."""
