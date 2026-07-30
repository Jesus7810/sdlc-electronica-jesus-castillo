from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ReadingModel


class SqlAlchemyReadingRepository:
    """Implementa la persistencia de lecturas mediante SQLAlchemy."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def add(
        self,
        sensor_id: str,
        value: float,
        unit: str,
    ) -> ReadingModel:
        reading = ReadingModel(
            sensor_id=sensor_id,
            value=value,
            unit=unit,
        )

        self._db.add(reading)
        self._db.commit()
        self._db.refresh(reading)

        return reading

    def list(
        self,
        sensor_id: str | None,
        skip: int,
        limit: int,
    ) -> list[ReadingModel]:
        statement = select(ReadingModel).order_by(ReadingModel.id)

        if sensor_id is not None:
            statement = statement.where(
                ReadingModel.sensor_id == sensor_id
            )

        statement = statement.offset(skip).limit(limit)

        return list(self._db.scalars(statement).all())

    def get_by_id(
        self,
        reading_id: int,
    ) -> ReadingModel | None:
        return self._db.get(ReadingModel, reading_id)

    def update(
        self,
        reading_id: int,
        value: float | None,
        unit: str | None,
    ) -> ReadingModel | None:
        reading = self.get_by_id(reading_id)

        if reading is None:
            return None

        if value is not None:
            reading.value = value

        if unit is not None:
            reading.unit = unit

        self._db.commit()
        self._db.refresh(reading)

        return reading

    def delete(
        self,
        reading_id: int,
    ) -> bool:
        reading = self.get_by_id(reading_id)

        if reading is None:
            return False

        self._db.delete(reading)
        self._db.commit()

        return True