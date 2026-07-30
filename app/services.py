from typing import Protocol

from app.models import ReadingModel


class ReadingRepository(Protocol):
    def add(
        self,
        sensor_id: str,
        value: float,
        unit: str,
    ) -> ReadingModel: ...

    def list_for_sensor(
        self,
        sensor_id: str,
    ) -> list[ReadingModel]: ...


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