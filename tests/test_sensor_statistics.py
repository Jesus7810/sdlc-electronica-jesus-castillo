from collections.abc import Generator
from datetime import UTC, datetime, timedelta

import pytest

from app.database import Base
from tests.test_main import client, test_engine


@pytest.fixture(autouse=True)
def prepare_statistics_database() -> Generator[None]:
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


def sensor_payload(sensor_id: str) -> dict[str, object]:
    return {
        "id": sensor_id,
        "name": "Sensor para estadísticas",
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


def create_reading(sensor_id: str, value: float, timestamp: str) -> dict[str, object]:
    response = client.post(
        f"/sensors/{sensor_id}/readings",
        json={"value": value, "unit": "C", "timestamp": timestamp},
    )
    assert response.status_code == 201
    return response.json()


def statistics_response(
    sensor_id: str,
    **params: object,
):
    return client.get(f"/sensors/{sensor_id}/readings/statistics", params=params)


def parse_utc(value: object) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    assert parsed.tzinfo is not None
    assert parsed.utcoffset() == timedelta(0)
    return parsed


def add_reference_readings(sensor_id: str) -> None:
    create_reading(sensor_id, 18.5, "2026-08-24T00:00:00Z")
    create_reading(sensor_id, 21.5, "2026-08-24T01:00:00Z")
    create_reading(sensor_id, 24.0, "2026-08-24T02:00:00Z")


def test_statistics_for_full_history_returns_aggregates_and_open_range() -> None:
    create_sensor("STAT-FULL-01")
    add_reference_readings("STAT-FULL-01")

    response = statistics_response("STAT-FULL-01")

    assert response.status_code == 200
    assert response.json() == {
        "sensor_id": "STAT-FULL-01",
        "unit": "C",
        "from_timestamp": None,
        "to_timestamp": None,
        "count": 3,
        "min_value": 18.5,
        "max_value": 24.0,
        "average_value": pytest.approx(64.0 / 3.0),
    }


def test_statistics_includes_readings_exactly_on_both_bounds() -> None:
    create_sensor("STAT-BOUNDS-01")
    add_reference_readings("STAT-BOUNDS-01")

    response = statistics_response(
        "STAT-BOUNDS-01",
        **{
            "from": "2026-08-24T00:00:00Z",
            "to": "2026-08-24T02:00:00Z",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 3
    assert body["min_value"] == 18.5
    assert body["max_value"] == 24.0
    assert parse_utc(body["from_timestamp"]) == datetime(2026, 8, 24, tzinfo=UTC)
    assert parse_utc(body["to_timestamp"]) == datetime(2026, 8, 24, 2, tzinfo=UTC)


@pytest.mark.parametrize(
    ("params", "expected_count", "expected_min", "expected_max"),
    [
        ({"from": "2026-08-24T01:00:00Z"}, 2, 21.5, 24.0),
        ({"to": "2026-08-24T01:00:00Z"}, 2, 18.5, 21.5),
        ({}, 3, 18.5, 24.0),
    ],
)
def test_statistics_supports_open_ended_and_unbounded_ranges(
    params: dict[str, str],
    expected_count: int,
    expected_min: float,
    expected_max: float,
) -> None:
    create_sensor("STAT-OPEN-RANGE-01")
    add_reference_readings("STAT-OPEN-RANGE-01")

    response = statistics_response("STAT-OPEN-RANGE-01", **params)

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == expected_count
    assert body["min_value"] == expected_min
    assert body["max_value"] == expected_max


def test_statistics_normalizes_offset_boundary_to_utc_before_filtering() -> None:
    create_sensor("STAT-OFFSET-01")
    create_reading("STAT-OFFSET-01", 18.0, "2026-08-24T09:00:00Z")
    create_reading("STAT-OFFSET-01", 24.0, "2026-08-24T10:00:00Z")

    response = statistics_response(
        "STAT-OFFSET-01",
        **{"from": "2026-08-24T05:00:00-05:00"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["min_value"] == 24.0
    assert body["max_value"] == 24.0
    assert parse_utc(body["from_timestamp"]) == datetime(2026, 8, 24, 10, tzinfo=UTC)
    assert body["to_timestamp"] is None


@pytest.mark.parametrize("parameter", ["from", "to"])
def test_statistics_rejects_naive_time_bounds(parameter: str) -> None:
    create_sensor("STAT-NAIVE-01")

    response = statistics_response(
        "STAT-NAIVE-01",
        **{parameter: "2026-08-24T10:00:00"},
    )

    assert response.status_code == 422


def test_statistics_rejects_range_inverted_after_utc_normalization() -> None:
    create_sensor("STAT-INVERTED-01")

    response = statistics_response(
        "STAT-INVERTED-01",
        **{
            "from": "2026-08-24T00:30:00-02:00",
            "to": "2026-08-24T01:00:00+02:00",
        },
    )

    assert response.status_code == 400


def test_statistics_for_empty_valid_period_returns_null_aggregates() -> None:
    create_sensor("STAT-EMPTY-01")

    response = statistics_response(
        "STAT-EMPTY-01",
        **{
            "from": "2026-08-24T00:00:00Z",
            "to": "2026-08-24T01:00:00Z",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 0
    assert body["min_value"] is None
    assert body["max_value"] is None
    assert body["average_value"] is None
    assert parse_utc(body["from_timestamp"]) == datetime(2026, 8, 24, tzinfo=UTC)
    assert parse_utc(body["to_timestamp"]) == datetime(2026, 8, 24, 1, tzinfo=UTC)


def test_statistics_for_unknown_sensor_returns_not_found() -> None:
    response = statistics_response("STAT-MISSING-01")

    assert response.status_code == 404


def test_statistics_are_available_for_inactive_sensor_history() -> None:
    create_sensor("STAT-INACTIVE-01")
    create_reading("STAT-INACTIVE-01", 22.0, "2026-08-24T10:00:00Z")
    assert client.post("/sensors/STAT-INACTIVE-01/deactivate").status_code == 200

    response = statistics_response("STAT-INACTIVE-01")

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["min_value"] == 22.0
    assert response.json()["max_value"] == 22.0


def test_statistics_returns_non_integer_average_with_float_precision() -> None:
    create_sensor("STAT-AVERAGE-01")
    create_reading("STAT-AVERAGE-01", 10.0, "2026-08-24T00:00:00Z")
    create_reading("STAT-AVERAGE-01", 10.0, "2026-08-24T01:00:00Z")
    create_reading("STAT-AVERAGE-01", 11.0, "2026-08-24T02:00:00Z")

    response = statistics_response("STAT-AVERAGE-01")

    assert response.status_code == 200
    assert response.json()["average_value"] == pytest.approx(31.0 / 3.0)


def test_statistics_does_not_modify_readings_or_alerts() -> None:
    create_sensor("STAT-READ-ONLY-01")
    create_reading("STAT-READ-ONLY-01", 35.0, "2026-08-24T10:00:00Z")
    readings_before = client.get("/sensors/STAT-READ-ONLY-01/readings").json()
    alerts_before = client.get("/alerts").json()

    response = statistics_response("STAT-READ-ONLY-01")

    assert response.status_code == 200
    assert client.get("/sensors/STAT-READ-ONLY-01/readings").json() == readings_before
    assert client.get("/alerts").json() == alerts_before
