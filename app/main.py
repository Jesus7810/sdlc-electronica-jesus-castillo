from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Annotated

from fastapi import Depends, FastAPI, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models  # noqa: F401
from app.database import Base, engine, get_db
from app.models import ReadingModel


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

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

@app.post("/readings", response_model=SensorReadingOut, status_code=201)
def create_reading(
    reading: SensorReadingIn,
    db: Annotated[Session, Depends(get_db)],
) -> SensorReadingOut:
    db_reading = ReadingModel(
        sensor_id=reading.sensor_id,
        value=reading.value,
        unit=reading.unit,
    )

    db.add(db_reading)
    db.commit()
    db.refresh(db_reading)

    return SensorReadingOut(
        id=db_reading.id,
        sensor_id=db_reading.sensor_id,
        value=db_reading.value,
        unit=db_reading.unit,
        timestamp=db_reading.timestamp,
    )

@app.get("/readings", response_model=list[SensorReadingOut])
def get_readings(
    db: Annotated[Session, Depends(get_db)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
) -> list[SensorReadingOut]:
    statement = (
        select(ReadingModel)
        .order_by(ReadingModel.id)
        .offset(skip)
        .limit(limit)
    )

    readings = db.scalars(statement).all()

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