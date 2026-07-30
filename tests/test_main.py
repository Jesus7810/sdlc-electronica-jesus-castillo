from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

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