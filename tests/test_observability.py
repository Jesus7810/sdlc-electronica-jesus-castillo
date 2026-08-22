import re
from collections.abc import Callable, Generator
from contextlib import contextmanager

import pytest
from sqlalchemy.exc import OperationalError, ProgrammingError, TimeoutError

from app.database import Base
from app.domain import DatabaseUnavailableError
from app.main import app
from app.repositories import SqlAlchemyOperationalRepository
from tests.test_main import client, test_engine


@pytest.fixture(autouse=True)
def prepare_observability_database() -> Generator[None]:
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


def sensor_payload(sensor_id: str) -> dict[str, object]:
    return {
        "id": sensor_id,
        "name": "Sensor para observabilidad",
        "location": "Laboratorio de pruebas",
        "type": "temperature",
        "unit": "C",
        "min_value": -40.0,
        "low_critical_threshold": 0.0,
        "low_warning_threshold": 10.0,
        "high_warning_threshold": 30.0,
        "high_critical_threshold": 40.0,
        "max_value": 80.0,
    }


def create_sensor(sensor_id: str) -> None:
    response = client.post("/sensors", json=sensor_payload(sensor_id))
    assert response.status_code == 201


def create_high_alert(sensor_id: str, timestamp: str) -> int:
    create_sensor(sensor_id)
    reading = client.post(
        f"/sensors/{sensor_id}/readings",
        json={"value": 35.0, "unit": "C", "timestamp": timestamp},
    )
    assert reading.status_code == 201
    alerts = client.get("/alerts", params={"sensor_id": sensor_id})
    assert alerts.status_code == 200
    return int(alerts.json()[0]["id"])


def metric_value(body: str, name: str) -> int:
    match = re.search(rf"^{name} ([0-9]+)$", body, re.MULTILINE)
    assert match is not None
    return int(match.group(1))


def assert_prometheus_format(body: str) -> None:
    for metric in (
        "sensorhub_active_sensors",
        "sensorhub_registered_readings",
        "sensorhub_unresolved_alerts",
    ):
        assert f"# HELP {metric} " in body
        assert f"# TYPE {metric} gauge" in body
        assert re.search(rf"^{metric} [0-9]+$", body, re.MULTILINE)
    assert body.endswith("\n")


def operational_dependency() -> Callable[..., object]:
    from app import routers

    dependency = getattr(routers, "get_operational_service", None)
    assert dependency is not None, "Falta la dependencia get_operational_service"
    return dependency


@contextmanager
def override_operational_service(service: object) -> Generator[None]:
    dependency = operational_dependency()
    app.dependency_overrides[dependency] = lambda: service
    try:
        yield
    finally:
        app.dependency_overrides.pop(dependency, None)


def unavailable_operational_service() -> object:
    operational_dependency()

    class UnavailableOperationalService:
        def ready(self) -> None:
            raise DatabaseUnavailableError(
                "postgresql://db-user:password@internal-host:5432/sensorhub "
                "SELECT * FROM sensors"
            )

        def metrics(self) -> object:
            raise DatabaseUnavailableError(
                "psycopg driver failed at internal-host with password"
            )

    return UnavailableOperationalService()


class FailingOperationalSession:
    def __init__(self, error: Exception) -> None:
        self._error = error

    def execute(self, statement: object) -> object:
        raise self._error


def operational_repository_that_fails(
    error: Exception,
) -> SqlAlchemyOperationalRepository:
    return SqlAlchemyOperationalRepository(FailingOperationalSession(error))  # type: ignore[arg-type]


def test_operational_repository_translates_sqlalchemy_pool_timeout() -> None:
    repository = operational_repository_that_fails(
        TimeoutError("QueuePool limit reached; connection acquisition timed out")
    )

    with pytest.raises(DatabaseUnavailableError):
        repository.ping()


@pytest.mark.parametrize(
    "message",
    (
        (
            'could not translate host name "database" to address: '
            "Name or service not known"
        ),
        "network is unreachable",
        "connection timeout expired",
    ),
)
def test_operational_repository_translates_connection_infrastructure_errors(
    message: str,
) -> None:
    repository = operational_repository_that_fails(
        OperationalError("SELECT 1", {}, Exception(message))
    )

    with pytest.raises(DatabaseUnavailableError):
        repository.ping()


@pytest.mark.parametrize(
    "error",
    (
        OperationalError("SELECT * FROM missing_table", {}, Exception("no such table")),
        ProgrammingError("SELECT invalid", {}, Exception("syntax error")),
    ),
)
def test_operational_repository_propagates_schema_and_programming_errors(
    error: Exception,
) -> None:
    repository = operational_repository_that_fails(error)

    with pytest.raises(type(error)):
        repository.ping()


def test_health_preserves_existing_liveness_contract() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_never_depends_on_operational_service_or_database() -> None:
    from app import routers

    dependency = getattr(routers, "get_operational_service", None)
    if dependency is None:
        response = client.get("/health")
    else:
        class BrokenOperationalService:
            def ready(self) -> None:
                raise AssertionError("health no debe consultar la base de datos")

            def metrics(self) -> object:
                raise AssertionError("health no debe consultar la base de datos")

        app.dependency_overrides[dependency] = lambda: BrokenOperationalService()
        try:
            response = client.get("/health")
        finally:
            app.dependency_overrides.pop(dependency, None)

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_returns_ready_when_database_is_available() -> None:
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_ready_hides_infrastructure_failure_details() -> None:
    service = unavailable_operational_service()

    with override_operational_service(service):
        response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
    response_text = response.text.lower()
    for forbidden in ("postgresql", "password", "internal-host", "select"):
        assert forbidden not in response_text


def test_metrics_without_data_returns_zero_prometheus_gauges() -> None:
    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain; version=0.0.4")
    assert_prometheus_format(response.text)
    assert metric_value(response.text, "sensorhub_active_sensors") == 0
    assert metric_value(response.text, "sensorhub_registered_readings") == 0
    assert metric_value(response.text, "sensorhub_unresolved_alerts") == 0


def test_metrics_count_active_sensors_readings_and_unresolved_alerts() -> None:
    open_alert = create_high_alert("OBS-OPEN-01", "2026-08-25T10:00:00Z")
    acknowledged_alert = create_high_alert("OBS-ACK-01", "2026-08-25T10:01:00Z")
    resolved_alert = create_high_alert("OBS-RESOLVED-01", "2026-08-25T10:02:00Z")
    assert client.post(f"/alerts/{acknowledged_alert}/acknowledge").status_code == 200
    assert client.post(f"/alerts/{resolved_alert}/resolve").status_code == 200
    create_sensor("OBS-INACTIVE-01")
    assert client.post("/sensors/OBS-INACTIVE-01/deactivate").status_code == 200

    response = client.get("/metrics")

    assert response.status_code == 200
    assert open_alert > 0
    assert metric_value(response.text, "sensorhub_active_sensors") == 3
    assert metric_value(response.text, "sensorhub_registered_readings") == 3
    assert metric_value(response.text, "sensorhub_unresolved_alerts") == 2


def test_metrics_uses_prometheus_help_type_values_and_final_newline() -> None:
    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain; version=0.0.4")
    assert_prometheus_format(response.text)


def test_metrics_hides_infrastructure_failure_details() -> None:
    service = unavailable_operational_service()

    with override_operational_service(service):
        response = client.get("/metrics")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
    response_text = response.text.lower()
    for forbidden in ("psycopg", "password", "internal-host", "driver"):
        assert forbidden not in response_text


def test_metrics_is_read_only_for_sensors_readings_and_alerts() -> None:
    create_high_alert("OBS-READ-ONLY-01", "2026-08-25T10:00:00Z")
    sensors_before = client.get("/sensors", params={"include_inactive": True}).json()
    readings_before = client.get("/sensors/OBS-READ-ONLY-01/readings").json()
    alerts_before = client.get("/alerts").json()

    response = client.get("/metrics")

    assert response.status_code == 200
    assert (
        client.get("/sensors", params={"include_inactive": True}).json()
        == sensors_before
    )
    assert client.get("/sensors/OBS-READ-ONLY-01/readings").json() == readings_before
    assert client.get("/alerts").json() == alerts_before
