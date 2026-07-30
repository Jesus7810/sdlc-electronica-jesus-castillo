from datetime import datetime

from sqlalchemy import DateTime, Float, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


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
    sensor_id: Mapped[str] = mapped_column(String(50), index=True)
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(20))
    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
    )
