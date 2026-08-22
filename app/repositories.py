from datetime import UTC, datetime, timedelta

from sqlalchemy import Select, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain import (
    AlertCondition,
    AlertSeverity,
    AlertStatus,
    Anomaly,
    ReadingAggregate,
)
from app.models import AlertModel, ReadingModel, SensorModel


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

    def list(self, include_inactive: bool = False) -> list[SensorModel]:
        statement = select(SensorModel).order_by(SensorModel.id)
        if not include_inactive:
            statement = statement.where(SensorModel.is_active.is_(True))
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


class SqlAlchemyReadingRepository:
    """Implementa la persistencia de lecturas mediante SQLAlchemy."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def add(
        self,
        sensor_id: str,
        value: float,
        unit: str,
        timestamp: datetime,
    ) -> ReadingModel:
        reading = ReadingModel(
            sensor_id=sensor_id,
            value=value,
            unit=unit,
            timestamp=timestamp,
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

    def has_for_sensor(self, sensor_id: str) -> bool:
        statement = select(ReadingModel.id).where(ReadingModel.sensor_id == sensor_id)
        return self._db.scalar(statement) is not None

    def all_within_range(
        self,
        sensor_id: str,
        min_value: float,
        max_value: float,
    ) -> bool:
        statement = select(ReadingModel.id).where(
            ReadingModel.sensor_id == sensor_id,
            (ReadingModel.value < min_value) | (ReadingModel.value > max_value),
        )
        return self._db.scalar(statement) is None

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
            statement = statement.where(ReadingModel.sensor_id == sensor_id)

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

    def statistics(
        self,
        sensor_id: str,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> ReadingAggregate:
        statement = select(
            func.count(ReadingModel.id).label("count"),
            func.min(ReadingModel.value).label("min_value"),
            func.max(ReadingModel.value).label("max_value"),
            func.avg(ReadingModel.value).label("average_value"),
        ).where(ReadingModel.sensor_id == sensor_id)
        if from_date is not None:
            statement = statement.where(ReadingModel.timestamp >= from_date)
        if to_date is not None:
            statement = statement.where(ReadingModel.timestamp <= to_date)
        result = self._db.execute(statement).one()._mapping
        return ReadingAggregate(
            count=int(result["count"]),
            min_value=(
                float(result["min_value"])
                if result["min_value"] is not None
                else None
            ),
            max_value=(
                float(result["max_value"])
                if result["max_value"] is not None
                else None
            ),
            average_value=(
                float(result["average_value"])
                if result["average_value"] is not None
                else None
            ),
        )

class SqlAlchemyAlertRepository:
    """Implementa la persistencia de alertas mediante SQLAlchemy."""

    def __init__(self, db: Session) -> None:
        self._db = db

    @staticmethod
    def _as_utc(timestamp: datetime) -> datetime:
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            return timestamp.replace(tzinfo=UTC)
        return timestamp.astimezone(UTC)

    def _unresolved_statement(
        self,
        sensor_id: str,
        condition: AlertCondition,
        lock: bool = False,
    ) -> Select[tuple[AlertModel]]:
        statement = select(AlertModel).where(
            AlertModel.sensor_id == sensor_id,
            AlertModel.condition == condition.value,
            AlertModel.status.in_(
                [
                    AlertStatus.OPEN.value,
                    AlertStatus.ACKNOWLEDGED.value,
                ]
            ),
        )
        if lock:
            statement = statement.with_for_update()
        return statement

    def _find_unresolved(
        self,
        sensor_id: str,
        condition: AlertCondition,
        lock: bool = False,
    ) -> AlertModel | None:
        return self._db.scalar(
            self._unresolved_statement(sensor_id, condition, lock=lock)
        )

    @staticmethod
    def _next_updated_at(alert: AlertModel) -> datetime:
        now = datetime.now(UTC)
        previous = SqlAlchemyAlertRepository._as_utc(alert.updated_at)
        if now <= previous:
            return previous + timedelta(microseconds=1)
        return now

    def _apply_evidence(
        self,
        alert: AlertModel,
        reading: ReadingModel,
        anomaly: Anomaly,
    ) -> None:
        if (
            alert.status == AlertStatus.ACKNOWLEDGED.value
            and alert.severity == AlertSeverity.WARNING.value
            and anomaly.severity == AlertSeverity.CRITICAL
        ):
            alert.status = AlertStatus.OPEN.value
        if anomaly.severity == AlertSeverity.CRITICAL:
            alert.severity = AlertSeverity.CRITICAL.value
        alert.last_reading_id = reading.id
        alert.last_reading_value = reading.value
        alert.last_threshold = anomaly.threshold
        alert.last_severity = anomaly.severity.value
        alert.last_triggered_at = self._as_utc(reading.timestamp)
        alert.updated_at = self._next_updated_at(alert)

    def _new_alert(self, reading: ReadingModel, anomaly: Anomaly) -> AlertModel:
        now = datetime.now(UTC)
        return AlertModel(
            sensor_id=reading.sensor_id,
            condition=anomaly.condition.value,
            severity=anomaly.severity.value,
            status=AlertStatus.OPEN.value,
            origin_reading_id=reading.id,
            origin_reading_value=reading.value,
            origin_threshold=anomaly.threshold,
            origin_severity=anomaly.severity.value,
            last_reading_id=reading.id,
            last_reading_value=reading.value,
            last_threshold=anomaly.threshold,
            last_severity=anomaly.severity.value,
            opened_at=now,
            last_triggered_at=self._as_utc(reading.timestamp),
            updated_at=now,
            acknowledged_at=None,
            resolved_at=None,
        )

    def open_or_update(
        self,
        reading: ReadingModel,
        anomaly: Anomaly,
    ) -> AlertModel:
        alert = self._find_unresolved(reading.sensor_id, anomaly.condition, lock=True)
        if alert is not None:
            self._apply_evidence(alert, reading, anomaly)
            self._db.commit()
            self._db.refresh(alert)
            return alert

        alert = self._new_alert(reading, anomaly)
        try:
            with self._db.begin_nested():
                self._db.add(alert)
                self._db.flush()
        except IntegrityError:
            alert = self._find_unresolved(
                reading.sensor_id,
                anomaly.condition,
                lock=True,
            )
            if alert is None:
                raise
            self._apply_evidence(alert, reading, anomaly)
        self._db.commit()
        self._db.refresh(alert)
        return alert

    def get_by_id(self, alert_id: int) -> AlertModel | None:
        return self._db.get(AlertModel, alert_id)

    def acknowledge(self, alert: AlertModel) -> AlertModel:
        changed_at = self._next_updated_at(alert)
        alert.status = AlertStatus.ACKNOWLEDGED.value
        if alert.acknowledged_at is None:
            alert.acknowledged_at = changed_at
        alert.updated_at = changed_at
        self._db.commit()
        self._db.refresh(alert)
        return alert

    def resolve(self, alert: AlertModel) -> AlertModel:
        changed_at = self._next_updated_at(alert)
        alert.status = AlertStatus.RESOLVED.value
        alert.resolved_at = changed_at
        alert.updated_at = changed_at
        self._db.commit()
        self._db.refresh(alert)
        return alert

    def list(
        self,
        sensor_id: str | None,
        status: AlertStatus | None,
        condition: AlertCondition | None,
        severity: AlertSeverity | None,
        offset: int,
        limit: int,
    ) -> list[AlertModel]:
        statement = select(AlertModel)
        if sensor_id is not None:
            statement = statement.where(AlertModel.sensor_id == sensor_id)
        if status is None:
            statement = statement.where(
                AlertModel.status.in_(
                    [
                        AlertStatus.OPEN.value,
                        AlertStatus.ACKNOWLEDGED.value,
                    ]
                )
            )
        else:
            statement = statement.where(AlertModel.status == status.value)
        if condition is not None:
            statement = statement.where(AlertModel.condition == condition.value)
        if severity is not None:
            statement = statement.where(AlertModel.severity == severity.value)
        statement = statement.order_by(
            AlertModel.opened_at.desc(),
            AlertModel.id.desc(),
        )
        statement = statement.offset(offset).limit(limit)
        return list(self._db.scalars(statement).all())
