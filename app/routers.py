import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.domain import (
    AlertCondition,
    AlertSeverity,
    AlertStatus,
    DatabaseUnavailableError,
    DomainValidationError,
    ResourceConflictError,
    ResourceNotFoundError,
)
from app.models import AlertModel, ReadingModel, SensorModel
from app.repositories import (
    SqlAlchemyAlertRepository,
    SqlAlchemyOperationalRepository,
    SqlAlchemyReadingRepository,
    SqlAlchemySensorRepository,
)
from app.schemas import (
    AlertOut,
    SensorCreate,
    SensorOut,
    SensorReadingCreate,
    SensorReadingIn,
    SensorReadingOut,
    SensorReadingStatisticsOut,
    SensorUpdate,
)
from app.services import (
    AlertRepository,
    AlertService,
    AlertStrategy,
    DatabaseAlertStrategy,
    InvalidDateRangeError,
    InvalidTimestampError,
    OperationalRepository,
    OperationalService,
    ReadingConflictError,
    ReadingRepository,
    ReadingService,
    SensorRepository,
    SensorService,
)

router = APIRouter()
logger = logging.getLogger(__name__)


def get_sensor_repository(
    db: Annotated[Session, Depends(get_db)],
) -> SensorRepository:
    return SqlAlchemySensorRepository(db)


def get_reading_repository(
    db: Annotated[Session, Depends(get_db)],
) -> ReadingRepository:
    return SqlAlchemyReadingRepository(db)


def get_alert_repository(
    db: Annotated[Session, Depends(get_db)],
) -> AlertRepository:
    return SqlAlchemyAlertRepository(db)


def get_operational_repository(
    db: Annotated[Session, Depends(get_db)],
) -> OperationalRepository:
    return SqlAlchemyOperationalRepository(db)


def get_operational_service(
    repo: Annotated[OperationalRepository, Depends(get_operational_repository)],
) -> OperationalService:
    return OperationalService(repo)


def get_alert_strategy(
    repo: Annotated[AlertRepository, Depends(get_alert_repository)],
) -> AlertStrategy:
    return DatabaseAlertStrategy(repo)


def get_alert_service(
    repo: Annotated[AlertRepository, Depends(get_alert_repository)],
) -> AlertService:
    return AlertService(repo)


def get_sensor_service(
    repo: Annotated[SensorRepository, Depends(get_sensor_repository)],
    reading_repo: Annotated[ReadingRepository, Depends(get_reading_repository)],
) -> SensorService:
    return SensorService(repo, reading_repo)


def get_reading_service(
    reading_repo: Annotated[ReadingRepository, Depends(get_reading_repository)],
    sensor_repo: Annotated[SensorRepository, Depends(get_sensor_repository)],
    alert_strategy: Annotated[AlertStrategy, Depends(get_alert_strategy)],
) -> ReadingService:
    return ReadingService(reading_repo, sensor_repo, alert_strategy)


def sensor_out(sensor: SensorModel) -> SensorOut:
    return SensorOut.model_validate(sensor)


def reading_out(reading: ReadingModel) -> SensorReadingOut:
    return SensorReadingOut.model_validate(reading)


def alert_out(alert: AlertModel) -> AlertOut:
    return AlertOut.model_validate(alert)


@router.get("/alerts", response_model=list[AlertOut])
def list_alerts(
    service: Annotated[AlertService, Depends(get_alert_service)],
    sensor_id: str | None = None,
    status: AlertStatus | None = None,
    condition: AlertCondition | None = None,
    severity: AlertSeverity | None = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[AlertOut]:
    return [
        alert_out(alert)
        for alert in service.list(
            sensor_id,
            status,
            condition,
            severity,
            offset,
            limit,
        )
    ]


@router.get("/alerts/{alert_id}", response_model=AlertOut)
def get_alert(
    alert_id: int,
    service: Annotated[AlertService, Depends(get_alert_service)],
) -> AlertOut:
    try:
        return alert_out(service.get(alert_id))
    except ResourceNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/alerts/{alert_id}/acknowledge", response_model=AlertOut)
def acknowledge_alert(
    alert_id: int,
    service: Annotated[AlertService, Depends(get_alert_service)],
) -> AlertOut:
    try:
        return alert_out(service.acknowledge(alert_id))
    except ResourceNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ResourceConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.post("/alerts/{alert_id}/resolve", response_model=AlertOut)
def resolve_alert(
    alert_id: int,
    service: Annotated[AlertService, Depends(get_alert_service)],
) -> AlertOut:
    try:
        return alert_out(service.resolve(alert_id))
    except ResourceNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ResourceConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
def ready(
    service: Annotated[OperationalService, Depends(get_operational_service)],
) -> Response:
    try:
        service.ready()
    except DatabaseUnavailableError:
        logger.error("database_unavailable", extra={"endpoint": "ready"})
        return JSONResponse(status_code=503, content={"status": "unavailable"})
    return JSONResponse(status_code=200, content={"status": "ready"})


def prometheus_metrics(
    active_sensors: int,
    registered_readings: int,
    unresolved_alerts: int,
) -> str:
    return (
        "# HELP sensorhub_active_sensors Current number of active sensors.\n"
        "# TYPE sensorhub_active_sensors gauge\n"
        f"sensorhub_active_sensors {active_sensors}\n"
        "# HELP sensorhub_registered_readings Current number of persisted readings.\n"
        "# TYPE sensorhub_registered_readings gauge\n"
        f"sensorhub_registered_readings {registered_readings}\n"
        "# HELP sensorhub_unresolved_alerts Current number of unresolved alerts.\n"
        "# TYPE sensorhub_unresolved_alerts gauge\n"
        f"sensorhub_unresolved_alerts {unresolved_alerts}\n"
    )


@router.get("/metrics")
def metrics(
    service: Annotated[OperationalService, Depends(get_operational_service)],
) -> Response:
    try:
        snapshot = service.metrics()
    except DatabaseUnavailableError:
        logger.error("database_unavailable", extra={"endpoint": "metrics"})
        return JSONResponse(status_code=503, content={"status": "unavailable"})
    return Response(
        content=prometheus_metrics(
            snapshot.active_sensors,
            snapshot.registered_readings,
            snapshot.unresolved_alerts,
        ),
        media_type="text/plain; version=0.0.4",
    )


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
                data.location,
                data.type,
                data.unit,
                data.min_value,
                data.low_critical_threshold,
                data.low_warning_threshold,
                data.high_warning_threshold,
                data.high_critical_threshold,
                data.max_value,
            )
        )
    except ResourceConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.get("/sensors", response_model=list[SensorOut])
def list_sensors(
    service: Annotated[SensorService, Depends(get_sensor_service)],
    include_inactive: bool = False,
) -> list[SensorOut]:
    return [sensor_out(sensor) for sensor in service.list(include_inactive)]


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


@router.post("/sensors/{sensor_id}/deactivate", response_model=SensorOut)
def deactivate_sensor(
    sensor_id: str,
    service: Annotated[SensorService, Depends(get_sensor_service)],
) -> SensorOut:
    try:
        return sensor_out(service.deactivate(sensor_id))
    except ResourceNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/sensors/{sensor_id}/activate", response_model=SensorOut)
def activate_sensor(
    sensor_id: str,
    service: Annotated[SensorService, Depends(get_sensor_service)],
) -> SensorOut:
    try:
        return sensor_out(service.activate(sensor_id))
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
    except ResourceConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
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
        readings = service.list(sensor_id, offset, limit, from_date, to_date)
    except InvalidTimestampError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except InvalidDateRangeError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return [reading_out(reading) for reading in readings]


@router.get(
    "/sensors/{sensor_id}/readings/statistics",
    response_model=SensorReadingStatisticsOut,
)
def get_sensor_reading_statistics(
    sensor_id: str,
    service: Annotated[ReadingService, Depends(get_reading_service)],
    from_date: Annotated[datetime | None, Query(alias="from")] = None,
    to_date: Annotated[datetime | None, Query(alias="to")] = None,
) -> SensorReadingStatisticsOut:
    try:
        statistics = service.statistics(sensor_id, from_date, to_date)
    except ResourceNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except InvalidTimestampError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except InvalidDateRangeError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return SensorReadingStatisticsOut.model_validate(statistics)


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
