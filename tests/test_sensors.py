from collections.abc import Generator

import pytest

from app.database import Base
from tests.test_main import client, test_engine


@pytest.fixture(autouse=True)
def prepare_sensor_database() -> Generator[None]:
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


def sensor_payload(sensor_id: str = "TEMP-01") -> dict[str, object]:
    return {
        "id": sensor_id,
        "name": "Temperatura del laboratorio",
        "type": "temperature",
        "unit": "C",
        "min_value": -40.0,
        "max_value": 125.0,
    }


def test_swagger_is_available() -> None:
    response = client.get("/docs")

    assert response.status_code == 200
    assert "Swagger UI" in response.text


def test_create_list_and_get_sensor() -> None:
    created = client.post("/sensors", json=sensor_payload())

    assert created.status_code == 201
    assert created.json() == sensor_payload()
    assert client.get("/sensors").json() == [sensor_payload()]
    assert client.get("/sensors/TEMP-01").json() == sensor_payload()


def test_duplicate_sensor_id_returns_409() -> None:
    client.post("/sensors", json=sensor_payload())

    response = client.post("/sensors", json=sensor_payload())

    assert response.status_code == 409


def test_get_unknown_sensor_returns_404() -> None:
    response = client.get("/sensors/UNKNOWN")

    assert response.status_code == 404


def test_patch_sensor_updates_only_sent_fields() -> None:
    client.post("/sensors", json=sensor_payload())

    response = client.patch(
        "/sensors/TEMP-01",
        json={"name": "Cámara fría", "min_value": -80.0},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Cámara fría"
    assert response.json()["min_value"] == -80.0
    assert response.json()["max_value"] == 125.0


def test_delete_sensor() -> None:
    client.post("/sensors", json=sensor_payload())

    response = client.delete("/sensors/TEMP-01")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get("/sensors/TEMP-01").status_code == 404


def test_delete_unknown_sensor_returns_404() -> None:
    assert client.delete("/sensors/UNKNOWN").status_code == 404


def test_rejects_invalid_sensor_range() -> None:
    payload = sensor_payload()
    payload["min_value"] = 125.0

    response = client.post("/sensors", json=payload)

    assert response.status_code == 422


def test_rejects_incompatible_type_and_unit() -> None:
    payload = sensor_payload()
    payload["unit"] = "%"

    response = client.post("/sensors", json=payload)

    assert response.status_code == 422


def test_humidity_accepts_percent_unit() -> None:
    payload = {
        "id": "HUM-01",
        "name": "Humedad",
        "type": "humidity",
        "unit": "%",
        "min_value": 0.0,
        "max_value": 100.0,
    }

    assert client.post("/sensors", json=payload).status_code == 201


def test_reading_requires_existing_sensor() -> None:
    response = client.post(
        "/sensors/UNKNOWN/readings",
        json={"value": 20.0, "unit": "C"},
    )

    assert response.status_code == 404


def test_reading_validates_unit_and_operating_range() -> None:
    client.post("/sensors", json=sensor_payload())

    valid = client.post(
        "/sensors/TEMP-01/readings",
        json={"value": 25.5, "unit": "C"},
    )
    wrong_unit = client.post(
        "/sensors/TEMP-01/readings",
        json={"value": 25.5, "unit": "%"},
    )
    below = client.post(
        "/sensors/TEMP-01/readings",
        json={"value": -40.1, "unit": "C"},
    )
    above = client.post(
        "/sensors/TEMP-01/readings",
        json={"value": 125.1, "unit": "C"},
    )

    assert valid.status_code == 201
    assert wrong_unit.status_code == 400
    assert below.status_code == 400
    assert above.status_code == 400


def test_integrated_sensor_reading_flow() -> None:
    client.post("/sensors", json=sensor_payload())
    created = client.post(
        "/sensors/TEMP-01/readings",
        json={"value": 25.5, "unit": "C"},
    )

    response = client.get(f"/readings/{created.json()['id']}")

    assert response.status_code == 200
    assert response.json()["sensor_id"] == "TEMP-01"
    assert response.json()["value"] == 25.5


@pytest.mark.parametrize("value", [-40.0, 125.0])
def test_reading_accepts_operating_range_boundaries(value: float) -> None:
    client.post("/sensors", json=sensor_payload())

    response = client.post(
        "/sensors/TEMP-01/readings",
        json={"value": value, "unit": "C"},
    )

    assert response.status_code == 201


@pytest.mark.parametrize(
    "reading",
    [
        {"value": 20.0, "unit": "%"},
        {"value": 126.0, "unit": "C"},
    ],
)
def test_rejected_reading_is_not_persisted(
    reading: dict[str, object],
) -> None:
    client.post("/sensors", json=sensor_payload())

    assert client.post(
        "/sensors/TEMP-01/readings", json=reading
    ).status_code == 400
    assert client.get("/sensors/TEMP-01/readings").json() == []


@pytest.mark.parametrize(
    "changes",
    [{"unit": "%"}, {"value": 126.0}],
)
def test_patch_reading_revalidates_sensor_rules(
    changes: dict[str, object],
) -> None:
    client.post("/sensors", json=sensor_payload())
    created = client.post(
        "/sensors/TEMP-01/readings",
        json={"value": 20.0, "unit": "C"},
    )

    response = client.patch(
        f"/readings/{created.json()['id']}", json=changes
    )

    assert response.status_code == 400
    persisted = client.get(f"/readings/{created.json()['id']}").json()
    assert persisted["value"] == 20.0
    assert persisted["unit"] == "C"


def test_patch_sensor_rejects_invalid_final_configuration() -> None:
    client.post("/sensors", json=sensor_payload())

    response = client.patch(
        "/sensors/TEMP-01", json={"min_value": 125.0}
    )

    assert response.status_code == 400


def test_patch_type_and_unit_without_readings() -> None:
    client.post("/sensors", json=sensor_payload())

    response = client.patch(
        "/sensors/TEMP-01",
        json={
            "type": "humidity",
            "unit": "%",
            "min_value": 0.0,
            "max_value": 100.0,
        },
    )

    assert response.status_code == 200
    assert response.json()["type"] == "humidity"
    assert response.json()["unit"] == "%"


def test_patch_type_or_unit_conflicts_with_existing_readings() -> None:
    client.post("/sensors", json=sensor_payload())
    client.post(
        "/sensors/TEMP-01/readings",
        json={"value": 20.0, "unit": "C"},
    )

    response = client.patch(
        "/sensors/TEMP-01",
        json={"type": "humidity", "unit": "%"},
    )

    assert response.status_code == 409


def test_patch_same_type_and_unit_is_not_a_conflict() -> None:
    client.post("/sensors", json=sensor_payload())
    client.post(
        "/sensors/TEMP-01/readings",
        json={"value": 20.0, "unit": "C"},
    )

    response = client.patch(
        "/sensors/TEMP-01",
        json={"type": "temperature", "unit": "C"},
    )

    assert response.status_code == 200


def test_patch_range_rejects_excluded_historical_reading() -> None:
    client.post("/sensors", json=sensor_payload())
    client.post(
        "/sensors/TEMP-01/readings",
        json={"value": 20.0, "unit": "C"},
    )

    response = client.patch(
        "/sensors/TEMP-01", json={"min_value": 21.0}
    )

    assert response.status_code == 409


def test_patch_range_accepts_all_historical_readings() -> None:
    client.post("/sensors", json=sensor_payload())
    client.post(
        "/sensors/TEMP-01/readings",
        json={"value": 20.0, "unit": "C"},
    )

    response = client.patch(
        "/sensors/TEMP-01",
        json={"min_value": 0.0, "max_value": 100.0},
    )

    assert response.status_code == 200


def test_delete_sensor_cascades_to_readings() -> None:
    client.post("/sensors", json=sensor_payload())
    created = client.post(
        "/sensors/TEMP-01/readings",
        json={"value": 20.0, "unit": "C"},
    )

    assert client.delete("/sensors/TEMP-01").status_code == 204
    assert client.get(f"/readings/{created.json()['id']}").status_code == 404


def test_legacy_create_requires_existing_sensor() -> None:
    response = client.post(
        "/readings",
        json={"sensor_id": "UNKNOWN", "value": 20.0, "unit": "C"},
    )

    assert response.status_code == 404


def test_sqlite_foreign_keys_are_enabled() -> None:
    with test_engine.connect() as connection:
        enabled = connection.exec_driver_sql("PRAGMA foreign_keys").scalar()

    assert enabled == 1


def test_openapi_contains_required_routes() -> None:
    paths = client.get("/openapi.json").json()["paths"]

    assert {
        "/sensors",
        "/sensors/{sensor_id}",
        "/sensors/{sensor_id}/readings",
        "/readings/{reading_id}",
    } <= paths.keys()
