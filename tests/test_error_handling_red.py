import json
import logging
import os
import subprocess
import sys
from collections.abc import Generator
from contextlib import contextmanager
from io import StringIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.domain import (
    DatabaseUnavailableError,
    DomainValidationError,
    ResourceConflictError,
    ResourceNotFoundError,
)
from app.main import app
from app.routers import get_operational_service
from app.services import (
    InvalidDateRangeError,
    InvalidTimestampError,
    ReadingConflictError,
)


@pytest.fixture
def response_client() -> Generator[TestClient]:
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.fixture
def app_log_output() -> Generator[StringIO]:
    app_logger = logging.getLogger("app")
    handlers = [
        handler
        for handler in app_logger.handlers
        if getattr(handler, "_sensorhub_json_handler", False)
    ]
    assert len(handlers) == 1
    handler = handlers[0]
    assert isinstance(handler, logging.StreamHandler)
    output = StringIO()
    previous_stream = handler.setStream(output)
    try:
        yield output
    finally:
        handler.setStream(previous_stream)


@contextmanager
def endpoint_that_raises(error: Exception) -> Generator[str]:
    path = f"/_test/global-error-handler/{type(error).__name__}"
    original_route_count = len(app.router.routes)

    def raise_error() -> None:
        raise error

    app.add_api_route(path, raise_error, methods=["GET"])
    try:
        yield path
    finally:
        del app.router.routes[original_route_count:]
        app.openapi_schema = None


def formatted_json_log(record: logging.LogRecord) -> tuple[str, dict[str, object]]:
    from app.logging import JsonFormatter

    json_line = JsonFormatter().format(record)
    assert "\n" not in json_line
    payload = json.loads(json_line)
    assert isinstance(payload, dict)
    return json_line, payload


def emitted_json_log(output: StringIO) -> tuple[str, dict[str, object]]:
    json_lines = output.getvalue().splitlines()
    assert len(json_lines) == 1
    json_line = json_lines[0]
    payload = json.loads(json_line)
    assert isinstance(payload, dict)
    return json_line, payload


def assert_safe_structured_error_log(
    output: StringIO,
    expected_fields: dict[str, object],
    forbidden_values: tuple[str, ...],
) -> None:
    json_line, payload = emitted_json_log(output)

    for field, expected_value in expected_fields.items():
        assert payload[field] == expected_value
    lowercase_json_line = json_line.lower()
    for forbidden in forbidden_values:
        assert forbidden not in lowercase_json_line


def test_app_logger_emits_json_once_without_root_propagation(
    app_log_output: StringIO,
) -> None:
    class RootRecordingHandler(logging.Handler):
        def __init__(self) -> None:
            super().__init__()
            self.records: list[logging.LogRecord] = []

        def emit(self, record: logging.LogRecord) -> None:
            self.records.append(record)

    root_handler = RootRecordingHandler()
    root_logger = logging.getLogger()
    root_logger.addHandler(root_handler)
    try:
        logging.getLogger("app").error(
            "ignored message",
            extra={
                "event": "test_event",
                "status_code": 500,
                "path": "/test",
                "method": "GET",
                "error_type": "RuntimeError",
            },
        )
    finally:
        root_logger.removeHandler(root_handler)

    assert logging.getLogger("app").propagate is False
    assert root_handler.records == []
    assert_safe_structured_error_log(
        app_log_output,
        {
            "event": "test_event",
            "status_code": 500,
            "path": "/test",
            "method": "GET",
            "error_type": "RuntimeError",
        },
        ("ignored message",),
    )


def test_json_formatter_emits_one_valid_json_line_with_error_extras() -> None:
    record = logging.makeLogRecord(
        {
            "msg": "error event",
            "event": "database_unavailable",
            "status_code": 503,
            "path": "/ready",
            "method": "GET",
            "error_type": "DatabaseUnavailableError",
        }
    )

    json_line, payload = formatted_json_log(record)

    assert json_line.strip() == json_line
    for field, expected_value in {
        "event": "database_unavailable",
        "status_code": 503,
        "path": "/ready",
        "method": "GET",
        "error_type": "DatabaseUnavailableError",
    }.items():
        assert payload[field] == expected_value


@pytest.mark.parametrize(
    ("error", "expected_status_code"),
    [
        (ResourceNotFoundError("recurso no encontrado"), 404),
        (ResourceConflictError("recurso en conflicto"), 409),
        (ReadingConflictError("lectura en conflicto"), 409),
        (DomainValidationError("regla de dominio inválida"), 400),
        (InvalidDateRangeError("rango de fechas inválido"), 400),
        (InvalidTimestampError("marca de tiempo inválida"), 422),
    ],
)
def test_global_handlers_preserve_domain_error_contracts(
    response_client: TestClient,
    error: Exception,
    expected_status_code: int,
) -> None:
    with endpoint_that_raises(error) as path:
        response = response_client.get(path)

    assert response.status_code == expected_status_code
    assert response.json() == {"detail": str(error)}


def test_value_error_is_not_registered_as_a_global_handler() -> None:
    assert ValueError not in app.exception_handlers


def test_unexpected_error_returns_a_safe_http_response(
    response_client: TestClient,
) -> None:
    error = RuntimeError(
        "postgresql://db-user:password@internal-host:5432/sensorhub SELECT *"
    )

    with endpoint_that_raises(error) as path:
        response = response_client.get(path)

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    response_text = response.text.lower()
    for forbidden in ("postgresql", "password", "internal-host", "select"):
        assert forbidden not in response_text


def test_ready_emits_a_safe_structured_json_error_log(
    app_log_output: StringIO,
    response_client: TestClient,
) -> None:
    class UnavailableOperationalService:
        def ready(self) -> None:
            raise DatabaseUnavailableError(
                "postgresql://db-user:password@internal-host:5432/sensorhub SELECT *"
            )

        def metrics(self) -> object:
            raise AssertionError("metrics no debe invocarse")

    app.dependency_overrides[get_operational_service] = UnavailableOperationalService
    try:
        response = response_client.get("/ready")
    finally:
        app.dependency_overrides.pop(get_operational_service, None)

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
    assert_safe_structured_error_log(
        app_log_output,
        {
            "event": "database_unavailable",
            "status_code": 503,
            "path": "/ready",
            "method": "GET",
            "error_type": "DatabaseUnavailableError",
        },
        ("postgresql", "password", "internal-host", "select"),
    )


def test_metrics_emits_a_safe_structured_json_error_log(
    app_log_output: StringIO,
    response_client: TestClient,
) -> None:
    class UnavailableOperationalService:
        def ready(self) -> None:
            raise AssertionError("ready no debe invocarse")

        def metrics(self) -> object:
            raise DatabaseUnavailableError(
                "postgresql://db-user:password@internal-host:5432/sensorhub SELECT *"
            )

    app.dependency_overrides[get_operational_service] = UnavailableOperationalService
    try:
        response = response_client.get("/metrics")
    finally:
        app.dependency_overrides.pop(get_operational_service, None)

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
    assert_safe_structured_error_log(
        app_log_output,
        {
            "event": "database_unavailable",
            "status_code": 503,
            "path": "/metrics",
            "method": "GET",
            "error_type": "DatabaseUnavailableError",
        },
        ("postgresql", "password", "internal-host", "select"),
    )


def test_global_not_found_error_emits_a_safe_structured_json_log(
    app_log_output: StringIO,
    response_client: TestClient,
) -> None:
    error = ResourceNotFoundError("sensor secreto no encontrado")
    with endpoint_that_raises(error) as path:
        response = response_client.get(path)

    assert response.status_code == 404
    assert_safe_structured_error_log(
        app_log_output,
        {
            "event": "domain_error",
            "status_code": 404,
            "path": path,
            "method": "GET",
            "error_type": "ResourceNotFoundError",
        },
        ("sensor secreto no encontrado",),
    )


def test_unexpected_error_emits_a_safe_structured_json_error_log(
    app_log_output: StringIO,
    response_client: TestClient,
) -> None:
    error = RuntimeError("password for internal-host failed")
    with endpoint_that_raises(error) as path:
        response = response_client.get(path)

    assert response.status_code == 500
    assert_safe_structured_error_log(
        app_log_output,
        {
            "event": "unhandled_exception",
            "status_code": 500,
            "path": path,
            "method": "GET",
            "error_type": "RuntimeError",
        },
        ("password", "internal-host"),
    )


def test_database_url_is_required_with_a_clear_configuration_message() -> None:
    environment = os.environ.copy()
    environment.pop("DATABASE_URL", None)
    project_root = Path(__file__).resolve().parents[1]

    result = subprocess.run(
        [sys.executable, "-c", "import app.database"],
        cwd=project_root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "DATABASE_URL environment variable is required" in (
        result.stdout + result.stderr
    )
