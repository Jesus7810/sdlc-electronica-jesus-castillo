from datetime import UTC, datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain import (
    AlertCondition,
    AlertSeverity,
    AlertStatus,
    SensorType,
    validate_sensor_configuration,
)


class SensorBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    location: str = Field(min_length=1, max_length=255)
    type: SensorType
    unit: str = Field(min_length=1, max_length=20)
    min_value: float
    low_critical_threshold: float
    low_warning_threshold: float
    high_warning_threshold: float
    high_critical_threshold: float
    max_value: float

    @field_validator("location", mode="before")
    @classmethod
    def normalize_location(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @model_validator(mode="after")
    def validate_configuration(self) -> Self:
        validate_sensor_configuration(
            self.type,
            self.unit,
            self.min_value,
            self.low_critical_threshold,
            self.low_warning_threshold,
            self.high_warning_threshold,
            self.high_critical_threshold,
            self.max_value,
        )
        return self


class SensorCreate(SensorBase):
    id: str = Field(min_length=1, max_length=50)


class SensorOut(SensorCreate):
    model_config = ConfigDict(from_attributes=True)

    is_active: bool
    deactivated_at: datetime | None

    @field_validator("deactivated_at", mode="before")
    @classmethod
    def normalize_deactivated_at(cls, value: object) -> object:
        if not isinstance(value, datetime) or value.tzinfo is not None:
            return value
        return value.replace(tzinfo=UTC)


class SensorUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=100)
    location: str | None = Field(default=None, min_length=1, max_length=255)
    type: SensorType | None = None
    unit: str | None = Field(default=None, min_length=1, max_length=20)
    min_value: float | None = None
    low_critical_threshold: float | None = None
    low_warning_threshold: float | None = None
    high_warning_threshold: float | None = None
    high_critical_threshold: float | None = None
    max_value: float | None = None

    @field_validator("location", mode="before")
    @classmethod
    def normalize_location(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class SensorReadingCreate(BaseModel):
    value: float
    unit: str = Field(min_length=1, max_length=20)
    timestamp: datetime | None = None

    @field_validator("timestamp")
    @classmethod
    def normalize_timestamp(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("El timestamp debe incluir zona horaria")
        return value.astimezone(UTC)


class SensorReadingIn(BaseModel):
    sensor_id: str = Field(..., examples=["TEMP-01"])
    value: float
    unit: str = "C"


class SensorReadingOut(SensorReadingIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime

    @field_validator("timestamp", mode="before")
    @classmethod
    def normalize_output_timestamp(cls, value: object) -> object:
        if not isinstance(value, datetime):
            return value
        if value.tzinfo is None or value.utcoffset() is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)


class SensorReadingStatisticsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sensor_id: str
    unit: str
    from_timestamp: datetime | None
    to_timestamp: datetime | None
    count: int
    min_value: float | None
    max_value: float | None
    average_value: float | None

    @field_validator("from_timestamp", "to_timestamp", mode="before")
    @classmethod
    def normalize_output_timestamp(cls, value: object) -> object:
        if not isinstance(value, datetime):
            return value
        if value.tzinfo is None or value.utcoffset() is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sensor_id: str
    condition: AlertCondition
    severity: AlertSeverity
    status: AlertStatus
    origin_reading_id: int
    origin_reading_value: float
    origin_threshold: float
    origin_severity: str
    last_reading_id: int
    last_reading_value: float
    last_threshold: float
    last_severity: str
    opened_at: datetime
    last_triggered_at: datetime
    updated_at: datetime
    acknowledged_at: datetime | None
    resolved_at: datetime | None

    @field_validator(
        "opened_at",
        "last_triggered_at",
        "updated_at",
        "acknowledged_at",
        "resolved_at",
        mode="before",
    )
    @classmethod
    def normalize_alert_timestamp(cls, value: object) -> object:
        if not isinstance(value, datetime):
            return value
        if value.tzinfo is None or value.utcoffset() is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
