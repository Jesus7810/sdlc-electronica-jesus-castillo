from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SensorModel(Base):
    __tablename__ = "sensors"
    __table_args__ = (
        CheckConstraint(
            "min_value < low_critical_threshold "
            "AND low_critical_threshold < low_warning_threshold "
            "AND low_warning_threshold < high_warning_threshold "
            "AND high_warning_threshold < high_critical_threshold "
            "AND high_critical_threshold < max_value",
            name="ck_sensors_threshold_order",
        ),
    )

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    location: Mapped[str] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(String(20))
    unit: Mapped[str] = mapped_column(String(20))
    min_value: Mapped[float] = mapped_column(Float)
    low_critical_threshold: Mapped[float] = mapped_column(Float)
    low_warning_threshold: Mapped[float] = mapped_column(Float)
    high_warning_threshold: Mapped[float] = mapped_column(Float)
    high_critical_threshold: Mapped[float] = mapped_column(Float)
    max_value: Mapped[float] = mapped_column(Float)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=true(),
        nullable=False,
        index=True,
    )
    deactivated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    readings: Mapped[list["ReadingModel"]] = relationship(
        back_populates="sensor",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class ReadingModel(Base):
    __tablename__ = "readings"
    __table_args__ = (
        UniqueConstraint(
            "sensor_id",
            "timestamp",
            name="uq_reading_sensor_timestamp",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    sensor_id: Mapped[str] = mapped_column(
        ForeignKey("sensors.id", ondelete="CASCADE"),
        index=True,
    )
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(20))
    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )
    sensor: Mapped[SensorModel] = relationship(back_populates="readings")


class AlertModel(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    sensor_id: Mapped[str] = mapped_column(
        ForeignKey("sensors.id", ondelete="CASCADE"),
        index=True,
    )
    reading_id: Mapped[int] = mapped_column(
        ForeignKey("readings.id", ondelete="CASCADE"),
        index=True,
    )
    reading_value: Mapped[float] = mapped_column(Float)
    threshold: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )
