from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.domain import (
    DomainValidationError,
    ResourceConflictError,
    ResourceNotFoundError,
)
from app.models import ReadingModel, SensorModel
from app.repositories import (
    SqlAlchemyReadingRepository,
    SqlAlchemySensorRepository,
)
from app.schemas import (
    SensorCreate,
    SensorOut,
    SensorReadingCreate,
    SensorReadingIn,
    SensorReadingOut,
    SensorReadingUpdate,
    SensorUpdate,
)
from app.services import (
    InvalidDateRangeError,
    ReadingConflictError,
    ReadingRepository,
    ReadingService,
    SensorRepository,
    SensorService,
)

router = APIRouter()


def get_sensor_repository(
    db: Annotated[Session, Depends(get_db)],
) -> SensorRepository:
    return SqlAlchemySensorRepository(db)


def get_reading_repository(
    db: Annotated[Session, Depends(get_db)],
) -> ReadingRepository:
    return SqlAlchemyReadingRepository(db)


def get_sensor_service(
    repo: Annotated[SensorRepository, Depends(get_sensor_repository)],
    reading_repo: Annotated[
        ReadingRepository, Depends(get_reading_repository)
    ],
) -> SensorService:
    return SensorService(repo, reading_repo)


def get_reading_service(
    reading_repo: Annotated[
        ReadingRepository, Depends(get_reading_repository)
    ],
    sensor_repo: Annotated[SensorRepository, Depends(get_sensor_repository)],
) -> ReadingService:
    return ReadingService(reading_repo, sensor_repo)


def sensor_out(sensor: SensorModel) -> SensorOut:
    return SensorOut.model_validate(sensor)


def reading_out(reading: ReadingModel) -> SensorReadingOut:
    return SensorReadingOut.model_validate(reading)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/sensors", response_model=SensorOut, status_code=201)
def create_sensor(
    data: SensorCreate,
    service: Annotated[SensorService, Depends(get_sensor_service)],
) -> SensorOut:
    try:
        return sensor_out(
            service.create(
                data.id,
                data.name,
                data.type,
                data.unit,
                data.min_value,
                data.max_value,
            )
        )
    except ResourceConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.get("/sensors", response_model=list[SensorOut])
def list_sensors(
    service: Annotated[SensorService, Depends(get_sensor_service)],
) -> list[SensorOut]:
    return [sensor_out(sensor) for sensor in service.list()]


@router.get("/sensors/{sensor_id}", response_model=SensorOut)
def get_sensor(
    sensor_id: str,
    service: Annotated[SensorService, Depends(get_sensor_service)],
) -> SensorOut:
    try:
        return sensor_out(service.get(sensor_id))
    except ResourceNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.patch("/sensors/{sensor_id}", response_model=SensorOut)
def update_sensor(
    sensor_id: str,
    changes: SensorUpdate,
    service: Annotated[SensorService, Depends(get_sensor_service)],
) -> SensorOut:
    try:
        return sensor_out(
            service.update(
                sensor_id,
                changes.model_dump(exclude_unset=True),
            )
        )
    except ResourceNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except DomainValidationError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except ResourceConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.delete("/sensors/{sensor_id}", status_code=204)
def delete_sensor(
    sensor_id: str,
    service: Annotated[SensorService, Depends(get_sensor_service)],
) -> None:
    try:
        service.delete(sensor_id)
    except ResourceNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


def record_reading(
    sensor_id: str,
    reading: SensorReadingCreate,
    service: ReadingService,
) -> SensorReadingOut:
    try:
        created = service.record(
            sensor_id,
            reading.value,
            reading.unit,
            reading.timestamp,
        )
    except ResourceNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except DomainValidationError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except ReadingConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return reading_out(created)


@router.post(
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


@router.post("/readings", response_model=SensorReadingOut, status_code=201)
def create_legacy_reading(
    reading: SensorReadingIn,
    service: Annotated[ReadingService, Depends(get_reading_service)],
) -> SensorReadingOut:
    return record_reading(
        reading.sensor_id,
        SensorReadingCreate(value=reading.value, unit=reading.unit),
        service,
    )


@router.get(
    "/sensors/{sensor_id}/readings",
    response_model=list[SensorReadingOut],
)
def list_sensor_readings(
    sensor_id: str,
    service: Annotated[ReadingService, Depends(get_reading_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    from_date: Annotated[datetime | None, Query(alias="from")] = None,
    to_date: Annotated[datetime | None, Query(alias="to")] = None,
) -> list[SensorReadingOut]:
    try:
        service.require_sensor(sensor_id)
    except ResourceNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    try:
        readings = service.list(
            sensor_id, offset, limit, from_date, to_date
        )
    except InvalidDateRangeError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return [reading_out(reading) for reading in readings]


@router.get("/readings", response_model=list[SensorReadingOut])
def list_legacy_readings(
    service: Annotated[ReadingService, Depends(get_reading_service)],
    sensor_id: str | None = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
) -> list[SensorReadingOut]:
    return [reading_out(item) for item in service.list(sensor_id, skip, limit)]


@router.get("/readings/{reading_id}", response_model=SensorReadingOut)
def get_reading(
    reading_id: int,
    service: Annotated[ReadingService, Depends(get_reading_service)],
) -> SensorReadingOut:
    reading = service.get(reading_id)
    if reading is None:
        raise HTTPException(status_code=404, detail="Lectura no encontrada")
    return reading_out(reading)


@router.patch("/readings/{reading_id}", response_model=SensorReadingOut)
def update_reading(
    reading_id: int,
    changes: SensorReadingUpdate,
    service: Annotated[ReadingService, Depends(get_reading_service)],
) -> SensorReadingOut:
    try:
        updated = service.update(reading_id, changes.value, changes.unit)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    if updated is None:
        raise HTTPException(status_code=404, detail="Lectura no encontrada")
    return reading_out(updated)


@router.delete("/readings/{reading_id}", status_code=204)
def delete_reading(
    reading_id: int,
    service: Annotated[ReadingService, Depends(get_reading_service)],
) -> None:
    if not service.delete(reading_id):
        raise HTTPException(status_code=404, detail="Lectura no encontrada")
