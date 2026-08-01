from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import SensorModel

TEST_DATABASE_URL = "sqlite://"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    expire_on_commit=False,
)


def override_get_db() -> Generator[Session]:
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def prepare_database() -> Generator[None]:
    Base.metadata.create_all(bind=test_engine)
    with TestingSessionLocal() as session:
        session.add_all(
            [
                SensorModel(
                    id="TEMP-01",
                    name="Temperatura",
                    type="temperature",
                    unit="C",
                    min_value=-273.15,
                    max_value=200.0,
                ),
                SensorModel(
                    id="TEMP-PATH",
                    name="Temperatura de ruta",
                    type="temperature",
                    unit="C",
                    min_value=-273.15,
                    max_value=200.0,
                ),
                SensorModel(
                    id="OTHER",
                    name="Otro sensor",
                    type="temperature",
                    unit="C",
                    min_value=-273.15,
                    max_value=200.0,
                ),
                SensorModel(
                    id="HUM-01",
                    name="Humedad",
                    type="humidity",
                    unit="%",
                    min_value=0.0,
                    max_value=100.0,
                ),
            ]
        )
        session.commit()

    yield

    Base.metadata.drop_all(bind=test_engine)


def test_get_reading_returns_existing_reading() -> None:
    create_response = client.post(
        "/readings",
        json={
            "sensor_id": "TEMP-01",
            "value": 25.5,
            "unit": "C",
        },
    )
    reading_id = create_response.json()["id"]

    response = client.get(f"/readings/{reading_id}")

    assert response.status_code == 200
    assert response.json()["sensor_id"] == "TEMP-01"
    assert response.json()["value"] == 25.5
    assert response.json()["unit"] == "C"


def test_get_reading_returns_404_when_not_found() -> None:
    response = client.get("/readings/999")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Lectura no encontrada",
    }

def test_update_reading_changes_provided_fields() -> None:
    create_response = client.post(
        "/readings",
        json={
            "sensor_id": "TEMP-01",
            "value": 25.5,
            "unit": "C",
        },
    )
    reading_id = create_response.json()["id"]

    response = client.patch(
        f"/readings/{reading_id}",
        json={"value": 30.0},
    )

    assert response.status_code == 200
    assert response.json()["sensor_id"] == "TEMP-01"
    assert response.json()["value"] == 30.0
    assert response.json()["unit"] == "C"


def test_update_reading_returns_404_when_not_found() -> None:
    response = client.patch(
        "/readings/999",
        json={"value": 30.0},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Lectura no encontrada",
    }


def test_update_reading_returns_400_for_invalid_temperature() -> None:
    create_response = client.post(
        "/readings",
        json={
            "sensor_id": "TEMP-01",
            "value": 25.5,
            "unit": "C",
        },
    )
    reading_id = create_response.json()["id"]

    response = client.patch(
        f"/readings/{reading_id}",
        json={"value": -274.0},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Temperatura por debajo del cero absoluto",
    }

def test_delete_reading_removes_existing_reading() -> None:
    create_response = client.post(
        "/readings",
        json={
            "sensor_id": "TEMP-01",
            "value": 25.5,
            "unit": "C",
        },
    )
    reading_id = create_response.json()["id"]

    delete_response = client.delete(f"/readings/{reading_id}")

    assert delete_response.status_code == 204
    assert delete_response.content == b""

    get_response = client.get(f"/readings/{reading_id}")

    assert get_response.status_code == 404


def test_delete_reading_returns_404_when_not_found() -> None:
    response = client.delete("/readings/999")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Lectura no encontrada",
    }


def create_nested(
    sensor_id: str,
    value: float,
    timestamp: str,
) -> Response:
    return client.post(
        f"/sensors/{sensor_id}/readings",
        json={"value": value, "unit": "C", "timestamp": timestamp},
    )


def test_nested_create_uses_sensor_id_from_path() -> None:
    response = create_nested("TEMP-PATH", 21.5, "2026-07-01T10:00:00")

    assert response.status_code == 201
    assert response.json()["sensor_id"] == "TEMP-PATH"


def test_nested_list_filters_sensor_and_uses_default_pagination() -> None:
    for index in range(55):
        create_nested(
            "TEMP-01",
            float(index),
            f"2026-07-01T10:{index:02d}:00",
        )
    create_nested("OTHER", 99.0, "2026-07-01T11:00:00")

    response = client.get("/sensors/TEMP-01/readings")

    assert response.status_code == 200
    assert len(response.json()) == 50
    assert {item["sensor_id"] for item in response.json()} == {"TEMP-01"}


def test_nested_list_applies_limit_and_offset() -> None:
    for index in range(4):
        create_nested(
            "TEMP-01",
            float(index),
            f"2026-07-01T10:0{index}:00",
        )

    response = client.get(
        "/sensors/TEMP-01/readings",
        params={"limit": 2, "offset": 1},
    )

    assert [item["value"] for item in response.json()] == [1.0, 2.0]


@pytest.mark.parametrize(
    "params",
    [{"limit": 0}, {"limit": 101}, {"offset": -1}, {"from": "not-a-date"}],
)
def test_nested_list_rejects_invalid_query(params: dict[str, object]) -> None:
    response = client.get("/sensors/TEMP-01/readings", params=params)

    assert response.status_code == 422


@pytest.mark.parametrize(
    ("params", "expected"),
    [
        ({"from": "2026-07-02T00:00:00"}, [2.0, 3.0]),
        ({"to": "2026-07-02T00:00:00"}, [1.0, 2.0]),
        (
            {
                "from": "2026-07-02T00:00:00",
                "to": "2026-07-02T23:59:59",
            },
            [2.0],
        ),
    ],
)
def test_nested_list_filters_dates(
    params: dict[str, str],
    expected: list[float],
) -> None:
    create_nested("TEMP-01", 1.0, "2026-07-01T00:00:00")
    create_nested("TEMP-01", 2.0, "2026-07-02T00:00:00")
    create_nested("TEMP-01", 3.0, "2026-07-03T00:00:00")

    response = client.get("/sensors/TEMP-01/readings", params=params)

    assert response.status_code == 200
    assert [item["value"] for item in response.json()] == expected


def test_nested_list_rejects_inverted_date_range() -> None:
    response = client.get(
        "/sensors/TEMP-01/readings",
        params={
            "from": "2026-07-03T00:00:00",
            "to": "2026-07-01T00:00:00",
        },
    )

    assert response.status_code == 400
    assert "'from'" in response.json()["detail"]


def test_duplicate_sensor_timestamp_returns_conflict() -> None:
    first = create_nested("TEMP-01", 10.0, "2026-07-01T00:00:00")
    repeated_value_different_time = create_nested(
        "TEMP-01", 10.0, "2026-07-01T00:01:00"
    )
    conflict = create_nested("TEMP-01", 20.0, "2026-07-01T00:00:00")

    assert first.status_code == 201
    assert repeated_value_different_time.status_code == 201
    assert conflict.status_code == 409


def test_nested_create_rejects_invalid_body() -> None:
    response = client.post(
        "/sensors/TEMP-01/readings",
        json={"value": "not-a-number"},
    )

    assert response.status_code == 422
