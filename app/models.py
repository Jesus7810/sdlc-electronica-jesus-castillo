from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SensorModel(Base):
    __tablename__ = "sensors"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    type: Mapped[str] = mapped_column(String(20))
    unit: Mapped[str] = mapped_column(String(20))
    min_value: Mapped[float] = mapped_column(Float)
    max_value: Mapped[float] = mapped_column(Float)
    readings: Mapped[list["ReadingModel"]] = relationship(
        back_populates="sensor",
        cascade="all, delete-orphan",
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
        ForeignKey("sensors.id"),
        index=True,
    )
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(20))
    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )
    sensor: Mapped[SensorModel] = relationship(back_populates="readings")
