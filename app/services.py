from typing import Protocol

from app.models import ReadingModel


class ReadingRepository(Protocol):
    def add(
        self,
        sensor_id: str,
        value: float,
        unit: str,
    ) -> ReadingModel: ...

    def list(
        self,
        sensor_id: str | None,
        skip: int,
        limit: int,
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
    ) -> ReadingModel:
        if value < -273.15:
            raise ValueError(
                "Temperatura por debajo del cero absoluto"
            )

        return self._repo.add(sensor_id, value, unit)

    def get(self, reading_id: int) -> ReadingModel | None:
        return self._repo.get_by_id(reading_id)

    def list(
        self,
        sensor_id: str | None,
        skip: int,
        limit: int,
    ) -> list[ReadingModel]:
        return self._repo.list(sensor_id, skip, limit)

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