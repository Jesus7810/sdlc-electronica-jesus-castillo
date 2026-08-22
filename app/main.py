import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.domain import (
    DomainValidationError,
    ResourceConflictError,
    ResourceNotFoundError,
)
from app.logging import configure_app_logging
from app.routers import router
from app.services import (
    InvalidDateRangeError,
    InvalidTimestampError,
    ReadingConflictError,
)

logger = logging.getLogger(__name__)


def log_error(
    request: Request,
    error: Exception,
    status_code: int,
    event: str,
) -> None:
    logger.error(
        "request_error",
        extra={
            "event": event,
            "status_code": status_code,
            "path": request.url.path,
            "method": request.method,
            "error_type": type(error).__name__,
        },
    )


def domain_error_response(
    request: Request,
    error: Exception,
    status_code: int,
) -> JSONResponse:
    log_error(request, error, status_code, "domain_error")
    return JSONResponse(status_code=status_code, content={"detail": str(error)})

app = FastAPI(
    title="SensorHub API",
    version="0.2.0",
)
configure_app_logging()


@app.exception_handler(ResourceNotFoundError)
def handle_resource_not_found(
    request: Request,
    error: ResourceNotFoundError,
) -> JSONResponse:
    return domain_error_response(request, error, 404)


@app.exception_handler(ResourceConflictError)
def handle_resource_conflict(
    request: Request,
    error: ResourceConflictError,
) -> JSONResponse:
    return domain_error_response(request, error, 409)


@app.exception_handler(ReadingConflictError)
def handle_reading_conflict(
    request: Request,
    error: ReadingConflictError,
) -> JSONResponse:
    return domain_error_response(request, error, 409)


@app.exception_handler(DomainValidationError)
def handle_domain_validation(
    request: Request,
    error: DomainValidationError,
) -> JSONResponse:
    return domain_error_response(request, error, 400)


@app.exception_handler(InvalidDateRangeError)
def handle_invalid_date_range(
    request: Request,
    error: InvalidDateRangeError,
) -> JSONResponse:
    return domain_error_response(request, error, 400)


@app.exception_handler(InvalidTimestampError)
def handle_invalid_timestamp(
    request: Request,
    error: InvalidTimestampError,
) -> JSONResponse:
    return domain_error_response(request, error, 422)


@app.exception_handler(Exception)
def handle_unexpected_error(request: Request, error: Exception) -> JSONResponse:
    log_error(request, error, 500, "unhandled_exception")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


app.include_router(router)
