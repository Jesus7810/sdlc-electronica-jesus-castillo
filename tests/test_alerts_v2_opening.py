from collections.abc import Generator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app.database import Base
from app.domain import AlertCondition, AlertSeverity, Anomaly
from app.models import AlertModel, ReadingModel
from app.services import DatabaseAlertStrategy
from tests.test_main import TestingSessionLocal, client, test_engine


@pytest.fixture(autouse=True)
def prepare_alerts_v2_database() -> Generator[None]:
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


def sensor_payload(sensor_id: str) -> dict[str, object]:
    return {
        "id": sensor_id,
        "name": "Sensor para alertas v2",
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
    value: float,
    timestamp: str,
) -> dict[str, object]:
    response = client.post(
        f"/sensors/{sensor_id}/readings",
        json={"value": value, "unit": "C", "timestamp": timestamp},
    )
    assert response.status_code == 201
    return response.json()


def get_alerts() -> list[dict[str, object]]:
    response = client.get("/alerts")
    assert response.status_code == 200
    return response.json()


def parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    assert parsed.tzinfo is not None
    assert parsed.utcoffset() == timedelta(0)
    return parsed


def assert_alert_shape(alert: dict[str, object]) -> None:
    assert set(alert) == {
        "id",
        "sensor_id",
        "condition",
        "severity",
        "status",
        "origin_reading_id",
        "origin_reading_value",
        "origin_threshold",
        "origin_severity",
        "last_reading_id",
        "last_reading_value",
        "last_threshold",
        "last_severity",
        "opened_at",
        "last_triggered_at",
        "updated_at",
    }
    assert {"reading_id", "reading_value", "threshold", "created_at"}.isdisjoint(
        alert
    )


def assert_alert_evidence(
    alert: dict[str, object],
    reading: dict[str, object],
    condition: AlertCondition,
    severity: AlertSeverity,
    threshold: float,
) -> None:
    assert_alert_shape(alert)
    assert alert["sensor_id"] == reading["sensor_id"]
    assert alert["condition"] == condition.value
    assert alert["severity"] == severity.value
    assert alert["status"] == "open"
    assert alert["origin_reading_id"] == reading["id"]
    assert alert["origin_reading_value"] == reading["value"]
    assert alert["origin_threshold"] == threshold
    assert alert["origin_severity"] == severity.value
    assert alert["last_reading_id"] == reading["id"]
    assert alert["last_reading_value"] == reading["value"]
    assert alert["last_threshold"] == threshold
    assert alert["last_severity"] == severity.value
    assert parse_utc(str(alert["last_triggered_at"])) == parse_utc(
        str(reading["timestamp"])
    )
    opened_at = parse_utc(str(alert["opened_at"]))
    updated_at = parse_utc(str(alert["updated_at"]))
    assert opened_at <= updated_at


@pytest.mark.parametrize("value", [10.0, 30.0])
def test_exact_warning_thresholds_create_no_alert(value: float) -> None:
    sensor_id = f"ALERT-NORMAL-{value:.0f}"
    create_sensor(sensor_id)

    create_reading(sensor_id, value, "2026-08-23T10:00:00Z")

    assert get_alerts() == []


@pytest.mark.parametrize(
    ("sensor_id", "value", "condition", "severity", "threshold"),
    [
        ("ALERT-WARNING-LOW", 5.0, AlertCondition.LOW, AlertSeverity.WARNING, 10.0),
        (
            "ALERT-WARNING-HIGH",
            35.0,
            AlertCondition.HIGH,
            AlertSeverity.WARNING,
            30.0,
        ),
        ("ALERT-CRITICAL-LOW", 0.0, AlertCondition.LOW, AlertSeverity.CRITICAL, 0.0),
        (
            "ALERT-CRITICAL-HIGH",
            40.0,
            AlertCondition.HIGH,
            AlertSeverity.CRITICAL,
            40.0,
        ),
    ],
)
def test_first_anomaly_opens_an_alert_with_complete_evidence(
    sensor_id: str,
    value: float,
    condition: AlertCondition,
    severity: AlertSeverity,
    threshold: float,
) -> None:
    create_sensor(sensor_id)
    reading = create_reading(sensor_id, value, "2026-08-23T10:00:00Z")

    alerts = get_alerts()

    assert len(alerts) == 1
    assert_alert_evidence(alerts[0], reading, condition, severity, threshold)


def test_same_severity_updates_last_evidence_without_reopening_origin() -> None:
    create_sensor("ALERT-REPEAT-01")
    first = create_reading("ALERT-REPEAT-01", 5.0, "2026-08-23T10:00:00Z")
    original = get_alerts()[0]

    second = create_reading("ALERT-REPEAT-01", 6.0, "2026-08-23T10:01:00Z")
    updated = get_alerts()[0]

    assert updated["id"] == original["id"]
    assert updated["severity"] == AlertSeverity.WARNING.value
    assert updated["origin_reading_id"] == first["id"]
    assert updated["origin_reading_value"] == 5.0
    assert updated["origin_threshold"] == 10.0
    assert updated["origin_severity"] == AlertSeverity.WARNING.value
    assert updated["last_reading_id"] == second["id"]
    assert updated["last_reading_value"] == 6.0
    assert updated["last_threshold"] == 10.0
    assert updated["last_severity"] == AlertSeverity.WARNING.value
    assert parse_utc(str(updated["last_triggered_at"])) == parse_utc(
        str(second["timestamp"])
    )
    assert updated["opened_at"] == original["opened_at"]
    assert parse_utc(str(updated["updated_at"])) > parse_utc(
        str(original["updated_at"])
    )


def test_critical_then_warning_keeps_maximum_severity_and_updates_evidence() -> None:
    create_sensor("ALERT-LOWER-SEVERITY-01")
    first = create_reading("ALERT-LOWER-SEVERITY-01", 0.0, "2026-08-23T10:00:00Z")
    original = get_alerts()[0]

    second = create_reading("ALERT-LOWER-SEVERITY-01", 5.0, "2026-08-23T10:01:00Z")
    updated = get_alerts()[0]

    assert updated["id"] == original["id"]
    assert updated["severity"] == AlertSeverity.CRITICAL.value
    assert updated["origin_reading_id"] == first["id"]
    assert updated["last_reading_id"] == second["id"]
    assert updated["last_reading_value"] == 5.0
    assert updated["last_threshold"] == 10.0
    assert updated["last_severity"] == AlertSeverity.WARNING.value


def test_warning_escalates_to_critical_without_replacing_origin() -> None:
    create_sensor("ALERT-ESCALATE-01")
    first = create_reading("ALERT-ESCALATE-01", 5.0, "2026-08-23T10:00:00Z")
    original = get_alerts()[0]

    second = create_reading("ALERT-ESCALATE-01", 0.0, "2026-08-23T10:01:00Z")
    updated = get_alerts()[0]

    assert updated["id"] == original["id"]
    assert updated["severity"] == AlertSeverity.CRITICAL.value
    assert updated["origin_reading_id"] == first["id"]
    assert updated["origin_reading_value"] == 5.0
    assert updated["origin_threshold"] == 10.0
    assert updated["origin_severity"] == AlertSeverity.WARNING.value
    assert updated["last_reading_id"] == second["id"]
    assert updated["last_threshold"] == 0.0
    assert updated["last_severity"] == AlertSeverity.CRITICAL.value


def test_low_and_high_conditions_can_be_open_at_the_same_time() -> None:
    create_sensor("ALERT-COEXIST-01")
    low_reading = create_reading("ALERT-COEXIST-01", 5.0, "2026-08-23T10:00:00Z")
    high_reading = create_reading("ALERT-COEXIST-01", 35.0, "2026-08-23T10:01:00Z")

    alerts = get_alerts()
    alerts_by_condition = {str(alert["condition"]): alert for alert in alerts}

    assert set(alerts_by_condition) == {"low", "high"}
    assert_alert_evidence(
        alerts_by_condition["low"],
        low_reading,
        AlertCondition.LOW,
        AlertSeverity.WARNING,
        10.0,
    )
    assert_alert_evidence(
        alerts_by_condition["high"],
        high_reading,
        AlertCondition.HIGH,
        AlertSeverity.WARNING,
        30.0,
    )


def test_normal_reading_does_not_modify_an_open_alert() -> None:
    create_sensor("ALERT-NORMAL-AFTER-01")
    create_reading("ALERT-NORMAL-AFTER-01", 35.0, "2026-08-23T10:00:00Z")
    before = get_alerts()[0]

    create_reading("ALERT-NORMAL-AFTER-01", 20.0, "2026-08-23T10:01:00Z")

    assert get_alerts() == [before]


@dataclass
class InMemoryOpenAlert:
    reading: ReadingModel
    anomaly: Anomaly
    severity: AlertSeverity


class FakeAlertV2Repository:
    def __init__(self) -> None:
        self.alerts: dict[tuple[str, AlertCondition], InMemoryOpenAlert] = {}

    def open_or_update(self, reading: ReadingModel, anomaly: Anomaly) -> None:
        key = (reading.sensor_id, anomaly.condition)
        existing = self.alerts.get(key)
        if existing is None:
            self.alerts[key] = InMemoryOpenAlert(reading, anomaly, anomaly.severity)
            return
        if anomaly.severity == AlertSeverity.CRITICAL:
            existing.severity = AlertSeverity.CRITICAL
        existing.reading = reading
        existing.anomaly = anomaly


def test_alert_strategy_deduplicates_same_condition_without_http() -> None:
    repository = FakeAlertV2Repository()
    strategy = DatabaseAlertStrategy(repository)
    first = ReadingModel(
        id=1,
        sensor_id="ALERT-SERVICE-01",
        value=5.0,
        unit="C",
        timestamp=datetime(2026, 8, 23, 10, 0, tzinfo=UTC),
    )
    second = ReadingModel(
        id=2,
        sensor_id="ALERT-SERVICE-01",
        value=0.0,
        unit="C",
        timestamp=datetime(2026, 8, 23, 10, 1, tzinfo=UTC),
    )

    strategy.handle_anomaly(
        first,
        Anomaly(AlertCondition.LOW, AlertSeverity.WARNING, 10.0),
    )
    strategy.handle_anomaly(
        second,
        Anomaly(AlertCondition.LOW, AlertSeverity.CRITICAL, 0.0),
    )

    assert len(repository.alerts) == 1
    alert = repository.alerts[("ALERT-SERVICE-01", AlertCondition.LOW)]
    assert alert.reading == second
    assert alert.anomaly == Anomaly(
        AlertCondition.LOW,
        AlertSeverity.CRITICAL,
        0.0,
    )
    assert alert.severity == AlertSeverity.CRITICAL


def test_database_rejects_two_open_alerts_for_same_sensor_and_condition() -> None:
    create_sensor("ALERT-DATABASE-01")
    reading = create_reading("ALERT-DATABASE-01", 20.0, "2026-08-23T10:00:00Z")
    timestamp = datetime(2026, 8, 23, 10, 0, tzinfo=UTC)

    first = AlertModel(
        sensor_id="ALERT-DATABASE-01",
        condition="low",
        severity="WARNING",
        status="open",
        origin_reading_id=reading["id"],
        origin_reading_value=5.0,
        origin_threshold=10.0,
        origin_severity="WARNING",
        last_reading_id=reading["id"],
        last_reading_value=5.0,
        last_threshold=10.0,
        last_severity="WARNING",
        opened_at=timestamp,
        last_triggered_at=timestamp,
        updated_at=timestamp,
    )
    second = AlertModel(
        sensor_id="ALERT-DATABASE-01",
        condition="low",
        severity="WARNING",
        status="open",
        origin_reading_id=reading["id"],
        origin_reading_value=6.0,
        origin_threshold=10.0,
        origin_severity="WARNING",
        last_reading_id=reading["id"],
        last_reading_value=6.0,
        last_threshold=10.0,
        last_severity="WARNING",
        opened_at=timestamp,
        last_triggered_at=timestamp,
        updated_at=timestamp,
    )

    with TestingSessionLocal() as session:
        session.add(first)
        session.commit()
        session.add(second)
        with pytest.raises(IntegrityError):
            session.commit()
