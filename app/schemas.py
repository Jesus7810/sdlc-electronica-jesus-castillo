from datetime import datetime
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

SensorType = Literal["temperature", "humidity"]
VALID_UNITS: dict[str, str] = {"temperature": "C", "humidity": "%"}


class SensorBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    type: SensorType
    unit: str = Field(min_length=1, max_length=20)
    min_value: float
    max_value: float

    @model_validator(mode="after")
    def validate_configuration(self) -> Self:
        if self.min_value >= self.max_value:
            raise ValueError("min_value debe ser menor que max_value")
        if VALID_UNITS[self.type] != self.unit:
            raise ValueError("El tipo y la unidad no son compatibles")
        return self


class SensorCreate(SensorBase):
    id: str = Field(min_length=1, max_length=50)


class SensorOut(SensorCreate):
    model_config = ConfigDict(from_attributes=True)


class SensorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    type: SensorType | None = None
    unit: str | None = Field(default=None, min_length=1, max_length=20)
    min_value: float | None = None
    max_value: float | None = None


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
