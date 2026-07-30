from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app import models  # noqa: F401
from app.database import Base, engine, get_db
from app.repositories import SqlAlchemyReadingRepository
from app.services import (
    InvalidDateRangeError,
    ReadingConflictError,
    ReadingRepository,
    ReadingService,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="SensorHub API",
    version="0.1.0",
    lifespan=lifespan,
)

class SensorReadingIn(BaseModel):
    sensor_id: str = Field(..., examples=["TEMP-01"])
    value: float
    unit: str = "C"


class SensorReadingCreate(BaseModel):
    value: float
    unit: str = "C"
    timestamp: datetime | None = None


class SensorReadingOut(SensorReadingIn):
    id: int
    timestamp: datetime

class SensorReadingUpdate(BaseModel):
    value: float | None = None
    unit: str | None = None

def get_repository(
    db: Annotated[Session, Depends(get_db)],
) -> ReadingRepository:
    return SqlAlchemyReadingRepository(db)


def get_reading_service(
    repo: Annotated[ReadingRepository, Depends(get_repository)],
) -> ReadingService:
    return ReadingService(repo)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def to_reading_out(reading: models.ReadingModel) -> SensorReadingOut:
    return SensorReadingOut.model_validate(reading, from_attributes=True)


def record_reading(
    sensor_id: str,
    reading: SensorReadingCreate,
    service: ReadingService,
) -> SensorReadingOut:
    try:
        created = service.record(
            sensor_id=sensor_id,
            value=reading.value,
            unit=reading.unit,
            timestamp=reading.timestamp,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except ReadingConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return to_reading_out(created)


@app.post(
    "/sensors/{sensor_id}/readings",
    response_model=SensorReadingOut,
    status_code=201,
)
def create_sensor_reading(
    sensor_id: str,
    reading: SensorReadingCreate,
    service: Annotated[ReadingService, Depends(get_reading_service)],
) -> SensorReadingOut:
    return record_reading(sensor_id, reading, service)


@app.post("/readings", response_model=SensorReadingOut, status_code=201)
def create_reading(
    reading: SensorReadingIn,
    service: Annotated[
        ReadingService,
        Depends(get_reading_service),
    ],
) -> SensorReadingOut:
    return record_reading(
        reading.sensor_id,
        SensorReadingCreate(
            value=reading.value,
            unit=reading.unit,
        ),
        service,
    )


@app.get(
    "/sensors/{sensor_id}/readings",
    response_model=list[SensorReadingOut],
)
def get_sensor_readings(
    sensor_id: str,
    service: Annotated[ReadingService, Depends(get_reading_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    from_date: Annotated[datetime | None, Query(alias="from")] = None,
    to_date: Annotated[datetime | None, Query(alias="to")] = None,
) -> list[SensorReadingOut]:
    try:
        readings = service.list(
            sensor_id,
            offset,
            limit,
            from_date,
            to_date,
        )
    except InvalidDateRangeError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return [to_reading_out(reading) for reading in readings]

@app.get("/readings", response_model=list[SensorReadingOut])
def get_readings(
    service: Annotated[
        ReadingService,
        Depends(get_reading_service),
    ],
    sensor_id: str | None = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
) -> list[SensorReadingOut]:
    readings = service.list(sensor_id, skip, limit)

    return [
        to_reading_out(reading)
        for reading in readings
    ]

@app.get("/readings/{reading_id}", response_model=SensorReadingOut)
def get_reading(
    reading_id: int,
    service: Annotated[
        ReadingService,
        Depends(get_reading_service),
    ],
) -> SensorReadingOut:
    reading = service.get(reading_id)

    if reading is None:
        raise HTTPException(
            status_code=404,
            detail="Lectura no encontrada",
        )

    return to_reading_out(reading)

@app.patch("/readings/{reading_id}", response_model=SensorReadingOut)
def update_reading(
    reading_id: int,
    changes: SensorReadingUpdate,
    service: Annotated[
        ReadingService,
        Depends(get_reading_service),
    ],
) -> SensorReadingOut:
    try:
        updated = service.update(
            reading_id=reading_id,
            value=changes.value,
            unit=changes.unit,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    if updated is None:
        raise HTTPException(
            status_code=404,
            detail="Lectura no encontrada",
        )

    return to_reading_out(updated)

@app.delete("/readings/{reading_id}", status_code=204)
def delete_reading(
    reading_id: int,
    service: Annotated[
        ReadingService,
        Depends(get_reading_service),
    ],
) -> None:
    deleted = service.delete(reading_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Lectura no encontrada",
        )
