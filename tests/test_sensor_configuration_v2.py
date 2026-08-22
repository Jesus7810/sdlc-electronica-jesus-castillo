from collections.abc import Generator

import pytest

from app.database import Base
from app.domain import DomainValidationError, validate_sensor_configuration
from tests.test_main import client, test_engine


@pytest.fixture(autouse=True)
def prepare_sensor_configuration_database() -> Generator[None]:
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


def sensor_v2_payload(
    sensor_id: str = "TEMP-V2-01",
    **changes: object,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": sensor_id,
        "name": "Temperatura del laboratorio",
        "location": "Laboratorio A",
        "type": "temperature",
        "unit": "C",
        "min_value": -40.0,
        "low_critical_threshold": 0.0,
        "low_warning_threshold": 10.0,
        "high_warning_threshold": 30.0,
        "high_critical_threshold": 40.0,
        "max_value": 80.0,
    }
    payload.update(changes)
    return payload


def configuration_values(**changes: float) -> dict[str, float]:
    payload = sensor_v2_payload(**changes)
    return {
        field: payload[field]
        for field in (
            "min_value",
            "low_critical_threshold",
            "low_warning_threshold",
            "high_warning_threshold",
            "high_critical_threshold",
            "max_value",
        )
    }


def validate_v2_configuration(**changes: float) -> None:
    validate_sensor_configuration(
        sensor_type="temperature",
        unit="C",
        **configuration_values(**changes),
    )


def response_has_error_for_field(response: object, field: str) -> bool:
    details = response.json()["detail"]  # type: ignore[union-attr]
    return any(detail["loc"][-1] == field for detail in details)


def response_has_domain_validation_error(response: object) -> bool:
    details = response.json()["detail"]  # type: ignore[union-attr]
    return any(detail["type"] == "value_error" for detail in details)


def test_domain_accepts_valid_sensor_v2_configuration() -> None:
    validate_v2_configuration()


@pytest.mark.parametrize(
    ("case", "changes"),
    [
        ("min_and_low_critical", {"low_critical_threshold": -40.0}),
        ("low_critical_and_low_warning", {"low_warning_threshold": 0.0}),
        ("low_warning_and_high_warning", {"high_warning_threshold": 10.0}),
        ("high_warning_and_high_critical", {"high_critical_threshold": 30.0}),
        ("high_critical_and_max", {"max_value": 40.0}),
    ],
)
def test_domain_rejects_equal_consecutive_v2_limits(
    case: str,
    changes: dict[str, float],
) -> None:
    del case

    with pytest.raises(DomainValidationError):
        validate_v2_configuration(**changes)


@pytest.mark.parametrize(
    ("case", "changes"),
    [
        ("min_above_low_critical", {"low_critical_threshold": -41.0}),
        ("low_critical_above_low_warning", {"low_warning_threshold": -1.0}),
        ("low_warning_above_high_warning", {"high_warning_threshold": 9.0}),
        ("high_warning_above_high_critical", {"high_critical_threshold": 29.0}),
        ("high_critical_above_max", {"max_value": 39.0}),
    ],
)
def test_domain_rejects_inverted_consecutive_v2_limits(
    case: str,
    changes: dict[str, float],
) -> None:
    del case

    with pytest.raises(DomainValidationError):
        validate_v2_configuration(**changes)


def test_create_sensor_v2_returns_location_and_all_operating_thresholds() -> None:
    payload = sensor_v2_payload()

    response = client.post("/sensors", json=payload)

    assert response.status_code == 201
    body = response.json()
    for field in (
        "id",
        "name",
        "location",
        "type",
        "unit",
        "min_value",
        "low_critical_threshold",
        "low_warning_threshold",
        "high_warning_threshold",
        "high_critical_threshold",
        "max_value",
    ):
        assert body[field] == payload[field]


def test_create_sensor_v2_rejects_missing_location() -> None:
    payload = sensor_v2_payload()
    del payload["location"]

    response = client.post("/sensors", json=payload)

    assert response.status_code == 422
    assert response_has_error_for_field(response, "location")


@pytest.mark.parametrize("location", ["", "   "])
def test_create_sensor_v2_rejects_blank_location(location: str) -> None:
    response = client.post("/sensors", json=sensor_v2_payload(location=location))

    assert response.status_code == 422
    assert response_has_error_for_field(response, "location")


def test_create_sensor_v2_rejects_location_longer_than_255_characters() -> None:
    response = client.post(
        "/sensors",
        json=sensor_v2_payload(location="L" * 256),
    )

    assert response.status_code == 422
    assert response_has_error_for_field(response, "location")


def test_create_sensor_v2_rejects_invalid_threshold_chain() -> None:
    response = client.post(
        "/sensors",
        json=sensor_v2_payload(high_critical_threshold=30.0),
    )

    assert response.status_code == 422
    assert response_has_domain_validation_error(response)


def test_patch_sensor_v2_updates_location_and_preserves_unsent_limits() -> None:
    payload = sensor_v2_payload()
    created = client.post("/sensors", json=payload)
    assert created.status_code == 201

    response = client.patch(
        "/sensors/TEMP-V2-01",
        json={"location": "Laboratorio B"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["location"] == "Laboratorio B"
    for field in (
        "id",
        "name",
        "type",
        "unit",
        "min_value",
        "low_critical_threshold",
        "low_warning_threshold",
        "high_warning_threshold",
        "high_critical_threshold",
        "max_value",
    ):
        assert body[field] == payload[field]


def test_patch_sensor_v2_rejects_invalid_final_chain_without_persisting() -> None:
    payload = sensor_v2_payload()
    created = client.post("/sensors", json=payload)
    assert created.status_code == 201

    response = client.patch(
        "/sensors/TEMP-V2-01",
        json={
            "high_warning_threshold": 40.0,
            "high_critical_threshold": 40.0,
        },
    )

    assert response.status_code == 400
    persisted = client.get("/sensors/TEMP-V2-01").json()
    assert persisted["high_warning_threshold"] == payload["high_warning_threshold"]
    assert persisted["high_critical_threshold"] == payload[
        "high_critical_threshold"
    ]
