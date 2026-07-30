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
from app.services import ReadingRepository, ReadingService


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
class SensorReadingOut(SensorReadingIn):
    id: int
    timestamp: datetime

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

@app.post("/readings", response_model=SensorReadingOut, status_code=201)
def create_reading(
    reading: SensorReadingIn,
    service: Annotated[
        ReadingService,
        Depends(get_reading_service),
    ],
) -> SensorReadingOut:
    created = service.record(
        sensor_id=reading.sensor_id,
        value=reading.value,
        unit=reading.unit,
    )

    return SensorReadingOut(
        id=created.id,
        sensor_id=created.sensor_id,
        value=created.value,
        unit=created.unit,
        timestamp=created.timestamp,
    )

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
    readings = service.list(
        sensor_id=sensor_id,
        skip=skip,
        limit=limit,
    )

    return [
        SensorReadingOut(
            id=reading.id,
            sensor_id=reading.sensor_id,
            value=reading.value,
            unit=reading.unit,
            timestamp=reading.timestamp,
        )
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

    return SensorReadingOut(
        id=reading.id,
        sensor_id=reading.sensor_id,
        value=reading.value,
        unit=reading.unit,
        timestamp=reading.timestamp,
    )