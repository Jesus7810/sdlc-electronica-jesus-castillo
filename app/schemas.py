from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain import SensorType, validate_sensor_configuration


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


class SensorUpdate(BaseModel):
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


class SensorReadingIn(BaseModel):
    sensor_id: str = Field(..., examples=["TEMP-01"])
    value: float
    unit: str = "C"


class SensorReadingOut(SensorReadingIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime


class SensorReadingUpdate(BaseModel):
    value: float | None = None
    unit: str | None = Field(default=None, min_length=1, max_length=20)


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sensor_id: str
    reading_id: int
    reading_value: float
    threshold: float
    created_at: datetime
