from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import ReadingModel, SensorModel


class SqlAlchemySensorRepository:
    """Implementa la persistencia de sensores mediante SQLAlchemy."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def add(self, sensor: SensorModel) -> SensorModel:
        try:
            self._db.add(sensor)
            self._db.commit()
        except IntegrityError:
            self._db.rollback()
            raise
        self._db.refresh(sensor)
        return sensor

    def list(self) -> list[SensorModel]:
        statement = select(SensorModel).order_by(SensorModel.id)
        return list(self._db.scalars(statement).all())

    def get_by_id(self, sensor_id: str) -> SensorModel | None:
        return self._db.get(SensorModel, sensor_id)

    def update(
        self,
        sensor: SensorModel,
        changes: dict[str, object],
    ) -> SensorModel:
        for field, value in changes.items():
            setattr(sensor, field, value)
        self._db.commit()
        self._db.refresh(sensor)
        return sensor

    def delete(self, sensor: SensorModel) -> None:
        self._db.delete(sensor)
        self._db.commit()


class SqlAlchemyReadingRepository:
    """Implementa la persistencia de lecturas mediante SQLAlchemy."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def add(
        self,
        sensor_id: str,
        value: float,
        unit: str,
        timestamp: datetime | None = None,
    ) -> ReadingModel:
        reading = ReadingModel(
            sensor_id=sensor_id,
            value=value,
            unit=unit,
            **({"timestamp": timestamp} if timestamp is not None else {}),
        )

        try:
            self._db.add(reading)
            self._db.commit()
        except IntegrityError:
            self._db.rollback()
            raise
        self._db.refresh(reading)

        return reading

    def exists_at(self, sensor_id: str, timestamp: datetime) -> bool:
        statement = select(ReadingModel.id).where(
            ReadingModel.sensor_id == sensor_id,
            ReadingModel.timestamp == timestamp,
        )
        return self._db.scalar(statement) is not None

    def list(
        self,
        sensor_id: str | None,
        offset: int,
        limit: int,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> list[ReadingModel]:
        statement = select(ReadingModel).order_by(ReadingModel.id)

        if sensor_id is not None:
            statement = statement.where(
                ReadingModel.sensor_id == sensor_id
            )

        if from_date is not None:
            statement = statement.where(ReadingModel.timestamp >= from_date)
        if to_date is not None:
            statement = statement.where(ReadingModel.timestamp <= to_date)

        statement = statement.offset(offset).limit(limit)

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
