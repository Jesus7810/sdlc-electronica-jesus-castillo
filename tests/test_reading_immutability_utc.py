from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import pytest

from app.database import Base
from app.services import ReadingService
from tests.test_main import client, test_engine
from tests.test_services import (
    FakeAlertStrategy,
    FakeReadingRepository,
    FakeSensorRepository,
)


@pytest.fixture(autouse=True)
def prepare_reading_utc_database() -> Generator[None]:
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


def sensor_payload(sensor_id: str) -> dict[str, object]:
    return {
        "id": sensor_id,
        "name": "Sensor de lecturas UTC",
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


def create_reading(
    sensor_id: str,
    value: float = 20.0,
    timestamp: str | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {"value": value, "unit": "C"}
    if timestamp is not None:
        payload["timestamp"] = timestamp
    response = client.post(f"/sensors/{sensor_id}/readings", json=payload)
    assert response.status_code == 201
    return response.json()


def parse_received_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    assert parsed.tzinfo is not None
    return parsed


def assert_received_utc_timestamp(value: str, expected: datetime) -> None:
    received = parse_received_timestamp(value)

    assert received.utcoffset() == timedelta(0)
    assert received.astimezone(UTC) == expected


def test_reading_without_timestamp_is_created_in_utc() -> None:
    create_sensor("READ-UTC-AUTO-01")

    reading = create_reading("READ-UTC-AUTO-01")

    received = parse_received_timestamp(str(reading["timestamp"]))

    assert received.utcoffset() == timedelta(0)
    assert received.astimezone(UTC) == received


def test_naive_timestamp_is_rejected_without_persisting() -> None:
    create_sensor("READ-UTC-NAIVE-01")

    response = client.post(
        "/sensors/READ-UTC-NAIVE-01/readings",
        json={
            "value": 20.0,
            "unit": "C",
            "timestamp": "2026-08-22T10:00:00",
        },
    )

    assert response.status_code == 422
    assert client.get("/sensors/READ-UTC-NAIVE-01/readings").json() == []


def test_timestamp_with_offset_is_normalized_to_utc_in_response_and_storage() -> None:
    create_sensor("READ-UTC-OFFSET-01")

    created = create_reading(
        "READ-UTC-OFFSET-01",
        timestamp="2026-08-22T05:00:00-05:00",
    )
    fetched = client.get(f"/readings/{created['id']}")

    assert fetched.status_code == 200
    expected_utc = datetime(2026, 8, 22, 10, 0, tzinfo=UTC)
    assert_received_utc_timestamp(str(created["timestamp"]), expected_utc)
    assert_received_utc_timestamp(str(fetched.json()["timestamp"]), expected_utc)


def test_equivalent_timestamp_offsets_conflict_for_the_same_sensor() -> None:
    create_sensor("READ-UTC-UNIQUE-01")
    first = create_reading(
        "READ-UTC-UNIQUE-01",
        timestamp="2026-08-22T10:00:00Z",
    )

    repeated = client.post(
        "/sensors/READ-UTC-UNIQUE-01/readings",
        json={
            "value": 21.0,
            "unit": "C",
            "timestamp": "2026-08-22T05:00:00-05:00",
        },
    )

    assert repeated.status_code == 409
    readings = client.get("/sensors/READ-UTC-UNIQUE-01/readings").json()
    assert [reading["id"] for reading in readings] == [first["id"]]


@pytest.mark.parametrize("method", ["patch", "delete"])
@pytest.mark.parametrize("reading_id", [1, 999])
def test_reading_mutation_routes_are_not_public(
    method: str,
    reading_id: int,
) -> None:
    create_sensor("READ-IMMUTABLE-01")
    existing = create_reading("READ-IMMUTABLE-01")
    target_id = existing["id"] if reading_id == 1 else reading_id

    if method == "patch":
        response = client.patch(f"/readings/{target_id}", json={"value": 25.0})
    else:
        response = client.delete(f"/readings/{target_id}")

    assert response.status_code == 405


def test_rejected_delete_keeps_the_reading_available() -> None:
    create_sensor("READ-IMMUTABLE-KEEP-01")
    created = create_reading("READ-IMMUTABLE-KEEP-01")

    rejected = client.delete(f"/readings/{created['id']}")
    fetched = client.get(f"/readings/{created['id']}")

    assert rejected.status_code == 405
    assert fetched.status_code == 200
    assert fetched.json()["value"] == 20.0


@pytest.mark.parametrize("parameter", ["from", "to"])
def test_naive_reading_date_filter_is_rejected(parameter: str) -> None:
    create_sensor("READ-UTC-FILTER-NAIVE-01")

    response = client.get(
        "/sensors/READ-UTC-FILTER-NAIVE-01/readings",
        params={parameter: "2026-08-22T10:00:00"},
    )

    assert response.status_code == 422


def test_reading_date_filters_compare_normalized_utc_instants() -> None:
    create_sensor("READ-UTC-FILTER-OFFSET-01")
    create_reading(
        "READ-UTC-FILTER-OFFSET-01",
        value=20.0,
        timestamp="2026-08-22T00:00:00Z",
    )
    create_reading(
        "READ-UTC-FILTER-OFFSET-01",
        value=21.0,
        timestamp="2026-08-22T01:00:00Z",
    )

    response = client.get(
        "/sensors/READ-UTC-FILTER-OFFSET-01/readings",
        params={"from": "2026-08-22T01:00:00+01:00"},
    )

    assert response.status_code == 200
    assert [reading["value"] for reading in response.json()] == [20.0, 21.0]


def test_reading_date_range_is_rejected_after_utc_normalization() -> None:
    create_sensor("READ-UTC-RANGE-01")

    response = client.get(
        "/sensors/READ-UTC-RANGE-01/readings",
        params={
            "from": "2026-08-22T00:30:00-02:00",
            "to": "2026-08-22T01:00:00+02:00",
        },
    )

    assert response.status_code == 400


def test_service_rejects_naive_timestamp_before_persistence_or_alert() -> None:
    reading_repository = FakeReadingRepository()
    alert_strategy = FakeAlertStrategy()
    service = ReadingService(
        reading_repository,
        FakeSensorRepository(),
        alert_strategy,
    )

    with pytest.raises(ValueError, match="zona horaria"):
        service.record(
            "TEMP-01",
            31.0,
            "C",
            datetime(2026, 8, 22, 10, 0),
        )

    assert reading_repository._readings == []
    assert alert_strategy.handled_anomalies == []
