from collections.abc import Generator
from datetime import UTC, datetime

import pytest

from app.database import Base
from app.services import ReadingService, ResourceConflictError, SensorService
from tests.test_main import client, test_engine
from tests.test_services import (
    FakeAlertStrategy,
    FakeReadingRepository,
    FakeSensorRepository,
)


@pytest.fixture(autouse=True)
def prepare_sensor_lifecycle_database() -> Generator[None]:
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


def sensor_payload(sensor_id: str) -> dict[str, object]:
    return {
        "id": sensor_id,
        "name": "Temperatura de ciclo de vida",
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


def create_sensor(sensor_id: str) -> dict[str, object]:
    response = client.post("/sensors", json=sensor_payload(sensor_id))
    assert response.status_code == 201
    return response.json()


def utc_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def test_new_sensor_is_active_without_deactivation_timestamp() -> None:
    sensor = create_sensor("LIFE-NEW-01")

    assert sensor["is_active"] is True
    assert sensor["deactivated_at"] is None


def test_deactivate_sensor_is_idempotent_and_preserves_utc_timestamp() -> None:
    create_sensor("LIFE-DEACT-01")

    first = client.post("/sensors/LIFE-DEACT-01/deactivate")

    assert first.status_code == 200
    first_body = first.json()
    first_deactivated_at = utc_datetime(first_body["deactivated_at"])
    assert first_body["is_active"] is False
    assert first_deactivated_at.tzinfo is not None
    assert first_deactivated_at.utcoffset() == UTC.utcoffset(first_deactivated_at)

    repeated = client.post("/sensors/LIFE-DEACT-01/deactivate")

    assert repeated.status_code == 200
    assert repeated.json()["is_active"] is False
    assert repeated.json()["deactivated_at"] == first_body["deactivated_at"]


def test_activate_sensor_is_idempotent_and_clears_deactivation_timestamp() -> None:
    create_sensor("LIFE-ACT-01")
    assert client.post("/sensors/LIFE-ACT-01/deactivate").status_code == 200

    activated = client.post("/sensors/LIFE-ACT-01/activate")

    assert activated.status_code == 200
    assert activated.json()["is_active"] is True
    assert activated.json()["deactivated_at"] is None

    repeated = client.post("/sensors/LIFE-ACT-01/activate")

    assert repeated.status_code == 200
    assert repeated.json()["is_active"] is True
    assert repeated.json()["deactivated_at"] is None


@pytest.mark.parametrize("action", ["activate", "deactivate"])
def test_lifecycle_action_unknown_sensor_returns_domain_404(action: str) -> None:
    response = client.post(f"/sensors/LIFE-UNKNOWN-01/{action}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Sensor no encontrado"}


def test_list_sensors_hides_inactive_by_default_and_can_include_them() -> None:
    create_sensor("LIFE-LIST-ACTIVE-01")
    create_sensor("LIFE-LIST-INACTIVE-01")
    assert client.post("/sensors/LIFE-LIST-INACTIVE-01/deactivate").status_code == 200

    default_response = client.get("/sensors")
    included_response = client.get("/sensors", params={"include_inactive": True})

    assert [sensor["id"] for sensor in default_response.json()] == [
        "LIFE-LIST-ACTIVE-01"
    ]
    assert {sensor["id"] for sensor in included_response.json()} == {
        "LIFE-LIST-ACTIVE-01",
        "LIFE-LIST-INACTIVE-01",
    }


def test_get_sensor_returns_inactive_sensor() -> None:
    create_sensor("LIFE-GET-01")
    assert client.post("/sensors/LIFE-GET-01/deactivate").status_code == 200

    response = client.get("/sensors/LIFE-GET-01")

    assert response.status_code == 200
    assert response.json()["is_active"] is False


@pytest.mark.parametrize(
    "changes",
    [
        {"is_active": False},
        {"deactivated_at": "2026-08-21T12:00:00Z"},
    ],
)
def test_patch_cannot_change_sensor_lifecycle(changes: dict[str, object]) -> None:
    create_sensor("LIFE-PATCH-01")

    response = client.patch("/sensors/LIFE-PATCH-01", json=changes)

    assert response.status_code == 422


@pytest.mark.parametrize("sensor_id", ["LIFE-DELETE-01", "LIFE-UNKNOWN-02"])
def test_delete_sensor_is_not_part_of_the_public_contract(sensor_id: str) -> None:
    if sensor_id == "LIFE-DELETE-01":
        create_sensor(sensor_id)

    response = client.delete(f"/sensors/{sensor_id}")

    assert response.status_code == 405


def test_inactive_sensor_rejects_high_reading_without_losing_history() -> None:
    create_sensor("LIFE-HISTORY-01")
    first_reading = client.post(
        "/sensors/LIFE-HISTORY-01/readings",
        json={
            "value": 31.0,
            "unit": "C",
            "timestamp": "2026-08-21T10:00:00Z",
        },
    )
    assert first_reading.status_code == 201
    assert len(client.get("/alerts").json()) == 1
    assert client.post("/sensors/LIFE-HISTORY-01/deactivate").status_code == 200

    rejected = client.post(
        "/sensors/LIFE-HISTORY-01/readings",
        json={
            "value": 32.0,
            "unit": "C",
            "timestamp": "2026-08-21T10:01:00Z",
        },
    )

    assert rejected.status_code == 409
    assert len(client.get("/sensors/LIFE-HISTORY-01/readings").json()) == 1
    assert len(client.get("/alerts").json()) == 1


def test_reading_service_rejects_inactive_sensor_before_persistence_or_alert() -> None:
    sensor_repo = FakeSensorRepository()
    sensor = sensor_repo.get_by_id("TEMP-01")
    assert sensor is not None
    sensor.is_active = False
    sensor.deactivated_at = datetime(2026, 8, 21, 11, 0, tzinfo=UTC)
    reading_repo = FakeReadingRepository()
    alert_strategy = FakeAlertStrategy()
    service = ReadingService(reading_repo, sensor_repo, alert_strategy)

    with pytest.raises(ResourceConflictError):
        service.record(
            "TEMP-01",
            31.0,
            "C",
            datetime(2026, 8, 21, 11, 1, tzinfo=UTC),
        )

    assert reading_repo._readings == []
    assert alert_strategy.handled_anomalies == []


def test_sensor_service_lifecycle_is_idempotent() -> None:
    sensor_repo = FakeSensorRepository()
    service = SensorService(sensor_repo, FakeReadingRepository())

    first = service.deactivate("TEMP-01")
    assert first.is_active is False
    assert first.deactivated_at is not None
    first_deactivated_at = first.deactivated_at

    repeated = service.deactivate("TEMP-01")
    assert repeated.deactivated_at == first_deactivated_at

    activated = service.activate("TEMP-01")
    activated_again = service.activate("TEMP-01")

    assert activated.is_active is True
    assert activated.deactivated_at is None
    assert activated_again.is_active is True
    assert activated_again.deactivated_at is None
