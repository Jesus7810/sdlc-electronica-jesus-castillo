from collections.abc import Generator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import Base
from app.domain import AlertCondition, AlertSeverity, Anomaly
from app.models import AlertModel, ReadingModel, SensorModel
from app.repositories import SqlAlchemyAlertRepository
from tests.test_main import TestingSessionLocal, client, test_engine


@pytest.fixture(autouse=True)
def prepare_alert_management_database() -> Generator[None]:
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


def sensor_payload(sensor_id: str) -> dict[str, object]:
    return {
        "id": sensor_id,
        "name": "Sensor de gestión de alertas",
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


def get_alerts(**params: object) -> list[dict[str, object]]:
    response = client.get("/alerts", params=params)
    assert response.status_code == 200
    return response.json()


def open_warning(
    sensor_id: str,
    timestamp: str = "2026-08-24T10:00:00Z",
) -> dict[str, object]:
    create_sensor(sensor_id)
    create_reading(sensor_id, 5.0, timestamp)
    alerts = get_alerts()
    assert len(alerts) == 1
    return alerts[0]


def parse_utc(value: object) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    assert parsed.tzinfo is not None
    assert parsed.utcoffset() == timedelta(0)
    return parsed


def assert_same_instant(left: object, right: object) -> None:
    assert parse_utc(left) == parse_utc(right)


def test_acknowledge_open_alert_records_first_acknowledgement() -> None:
    alert = open_warning("ALERT-ACK-OPEN-01")
    original_updated_at = alert["updated_at"]
    original_last_triggered_at = alert["last_triggered_at"]

    response = client.post(f"/alerts/{alert['id']}/acknowledge")

    assert response.status_code == 200
    acknowledged = response.json()
    assert acknowledged["status"] == "acknowledged"
    assert parse_utc(acknowledged["acknowledged_at"]) > parse_utc(
        original_updated_at
    )
    assert parse_utc(acknowledged["updated_at"]) > parse_utc(original_updated_at)
    assert_same_instant(
        acknowledged["last_triggered_at"],
        original_last_triggered_at,
    )
    assert acknowledged["resolved_at"] is None


def test_acknowledge_repeated_or_resolved_alert_returns_conflict() -> None:
    alert = open_warning("ALERT-ACK-CONFLICT-01")
    first_response = client.post(f"/alerts/{alert['id']}/acknowledge")
    assert first_response.status_code == 200
    acknowledged = first_response.json()

    repeated = client.post(f"/alerts/{alert['id']}/acknowledge")

    assert repeated.status_code == 409
    assert client.get(f"/alerts/{alert['id']}").json() == acknowledged

    resolved = client.post(f"/alerts/{alert['id']}/resolve")
    assert resolved.status_code == 200
    resolved_snapshot = resolved.json()

    after_resolved = client.post(f"/alerts/{alert['id']}/acknowledge")

    assert after_resolved.status_code == 409
    assert client.get(f"/alerts/{alert['id']}").json() == resolved_snapshot


def test_acknowledge_unknown_alert_returns_not_found() -> None:
    response = client.post("/alerts/999999/acknowledge")

    assert response.status_code == 404


def test_resolve_open_alert_changes_only_lifecycle_timestamps() -> None:
    alert = open_warning("ALERT-RESOLVE-OPEN-01")
    original_updated_at = alert["updated_at"]
    original_last_triggered_at = alert["last_triggered_at"]

    response = client.post(f"/alerts/{alert['id']}/resolve")

    assert response.status_code == 200
    resolved = response.json()
    assert resolved["status"] == "resolved"
    assert resolved["acknowledged_at"] is None
    assert parse_utc(resolved["resolved_at"]) > parse_utc(original_updated_at)
    assert parse_utc(resolved["updated_at"]) > parse_utc(original_updated_at)
    assert_same_instant(resolved["last_triggered_at"], original_last_triggered_at)


def test_resolve_acknowledged_alert_preserves_acknowledged_at() -> None:
    alert = open_warning("ALERT-RESOLVE-ACK-01")
    acknowledged = client.post(f"/alerts/{alert['id']}/acknowledge")
    assert acknowledged.status_code == 200
    acknowledged_at = acknowledged.json()["acknowledged_at"]
    original_last_triggered_at = acknowledged.json()["last_triggered_at"]

    resolved = client.post(f"/alerts/{alert['id']}/resolve")

    assert resolved.status_code == 200
    body = resolved.json()
    assert body["status"] == "resolved"
    assert_same_instant(body["acknowledged_at"], acknowledged_at)
    assert parse_utc(body["resolved_at"]) <= parse_utc(body["updated_at"])
    assert_same_instant(body["last_triggered_at"], original_last_triggered_at)


def test_resolve_repeated_or_unknown_alert_returns_expected_error() -> None:
    alert = open_warning("ALERT-RESOLVE-CONFLICT-01")
    resolved = client.post(f"/alerts/{alert['id']}/resolve")
    assert resolved.status_code == 200
    snapshot = resolved.json()

    repeated = client.post(f"/alerts/{alert['id']}/resolve")

    assert repeated.status_code == 409
    assert client.get(f"/alerts/{alert['id']}").json() == snapshot
    assert client.post("/alerts/999999/resolve").status_code == 404


def test_acknowledged_same_or_lower_severity_keeps_state_and_updates_evidence() -> None:
    alert = open_warning("ALERT-ACK-EVIDENCE-01", "2026-08-24T10:00:00Z")
    acknowledged = client.post(f"/alerts/{alert['id']}/acknowledge")
    assert acknowledged.status_code == 200
    before = acknowledged.json()

    reading = create_reading("ALERT-ACK-EVIDENCE-01", 6.0, "2026-08-24T10:01:00Z")
    after = client.get(f"/alerts/{alert['id']}")

    assert after.status_code == 200
    body = after.json()
    assert body["status"] == "acknowledged"
    assert_same_instant(body["acknowledged_at"], before["acknowledged_at"])
    assert body["origin_reading_id"] == alert["origin_reading_id"]
    assert body["last_reading_id"] == reading["id"]
    assert body["last_reading_value"] == 6.0
    assert body["last_severity"] == "WARNING"
    assert_same_instant(body["last_triggered_at"], reading["timestamp"])
    assert parse_utc(body["updated_at"]) > parse_utc(before["updated_at"])


def test_acknowledged_warning_reopens_when_new_evidence_is_critical() -> None:
    alert = open_warning("ALERT-ACK-REOPEN-01", "2026-08-24T10:00:00Z")
    acknowledged = client.post(f"/alerts/{alert['id']}/acknowledge")
    assert acknowledged.status_code == 200
    before = acknowledged.json()

    critical = create_reading("ALERT-ACK-REOPEN-01", 0.0, "2026-08-24T10:01:00Z")
    after = client.get(f"/alerts/{alert['id']}")

    assert after.status_code == 200
    body = after.json()
    assert body["status"] == "open"
    assert body["severity"] == "CRITICAL"
    assert_same_instant(body["acknowledged_at"], before["acknowledged_at"])
    assert body["origin_reading_id"] == alert["origin_reading_id"]
    assert body["last_reading_id"] == critical["id"]
    assert body["last_severity"] == "CRITICAL"


@pytest.mark.parametrize("value", [5.0, 0.0])
def test_acknowledged_critical_remains_acknowledged_for_non_escalation(
    value: float,
) -> None:
    alert = open_warning("ALERT-ACK-CRITICAL-01", "2026-08-24T10:00:00Z")
    escalated = create_reading("ALERT-ACK-CRITICAL-01", 0.0, "2026-08-24T10:01:00Z")
    acknowledged = client.post(f"/alerts/{alert['id']}/acknowledge")
    assert acknowledged.status_code == 200

    later = create_reading("ALERT-ACK-CRITICAL-01", value, "2026-08-24T10:02:00Z")
    response = client.get(f"/alerts/{alert['id']}")

    assert response.status_code == 200
    body = response.json()
    assert escalated["id"] != later["id"]
    assert body["status"] == "acknowledged"
    assert body["severity"] == "CRITICAL"
    assert body["last_reading_id"] == later["id"]


def test_resolved_alert_allows_new_alert_with_new_origin() -> None:
    alert = open_warning("ALERT-RESOLVED-NEW-01", "2026-08-24T10:00:00Z")
    resolved = client.post(f"/alerts/{alert['id']}/resolve")
    assert resolved.status_code == 200

    reading = create_reading("ALERT-RESOLVED-NEW-01", 6.0, "2026-08-24T10:01:00Z")
    unresolved = get_alerts()

    assert len(unresolved) == 1
    reopened = unresolved[0]
    assert reopened["id"] != alert["id"]
    assert reopened["status"] == "open"
    assert reopened["origin_reading_id"] == reading["id"]
    assert reopened["acknowledged_at"] is None
    assert reopened["resolved_at"] is None


def make_sensor(sensor_id: str) -> SensorModel:
    return SensorModel(
        id=sensor_id,
        name="Sensor de consultas",
        location="Laboratorio de pruebas",
        type="temperature",
        unit="C",
        min_value=-40.0,
        low_critical_threshold=0.0,
        low_warning_threshold=10.0,
        high_warning_threshold=30.0,
        high_critical_threshold=40.0,
        max_value=80.0,
    )


def seed_alert(
    session: Session,
    sensor_id: str,
    condition: str,
    severity: str,
    status: str,
    opened_at: datetime,
) -> int:
    db = session
    sensor = make_sensor(sensor_id)
    db.add(sensor)
    db.flush()
    reading = ReadingModel(
        sensor_id=sensor_id,
        value=5.0,
        unit="C",
        timestamp=opened_at,
    )
    db.add(reading)
    db.flush()
    acknowledged_at = opened_at if status in {"acknowledged", "resolved"} else None
    resolved_at = opened_at if status == "resolved" else None
    alert = AlertModel(
        sensor_id=sensor_id,
        condition=condition,
        severity=severity,
        status=status,
        origin_reading_id=reading.id,
        origin_reading_value=reading.value,
        origin_threshold=10.0,
        origin_severity=severity,
        last_reading_id=reading.id,
        last_reading_value=reading.value,
        last_threshold=10.0,
        last_severity=severity,
        opened_at=opened_at,
        last_triggered_at=opened_at,
        updated_at=opened_at,
        acknowledged_at=acknowledged_at,
        resolved_at=resolved_at,
    )
    db.add(alert)
    db.commit()
    return alert.id


def test_list_alerts_defaults_to_unresolved_and_filters_independently() -> None:
    with TestingSessionLocal() as session:
        open_id = seed_alert(
            session,
            "ALERT-QUERY-A",
            "low",
            "WARNING",
            "open",
            datetime(2026, 8, 24, 10, 0, tzinfo=UTC),
        )
        acknowledged_id = seed_alert(
            session,
            "ALERT-QUERY-B",
            "high",
            "CRITICAL",
            "acknowledged",
            datetime(2026, 8, 24, 11, 0, tzinfo=UTC),
        )
        resolved_id = seed_alert(
            session,
            "ALERT-QUERY-C",
            "low",
            "WARNING",
            "resolved",
            datetime(2026, 8, 24, 12, 0, tzinfo=UTC),
        )

    assert {item["id"] for item in get_alerts()} == {open_id, acknowledged_id}
    assert [item["id"] for item in get_alerts(sensor_id="ALERT-QUERY-A")] == [
        open_id
    ]
    assert [item["id"] for item in get_alerts(status="resolved")] == [resolved_id]
    assert [item["id"] for item in get_alerts(condition="high")] == [
        acknowledged_id
    ]
    assert [item["id"] for item in get_alerts(severity="CRITICAL")] == [
        acknowledged_id
    ]


def test_alert_list_orders_then_applies_offset_and_limit_with_id_tie_breaker() -> None:
    timestamp = datetime(2026, 8, 24, 12, 0, tzinfo=UTC)
    with TestingSessionLocal() as session:
        oldest = seed_alert(
            session,
            "ALERT-PAGE-OLD",
            "low",
            "WARNING",
            "open",
            datetime(2026, 8, 24, 11, 0, tzinfo=UTC),
        )
        tied_first = seed_alert(
            session,
            "ALERT-PAGE-TIE-ONE",
            "low",
            "WARNING",
            "open",
            timestamp,
        )
        tied_second = seed_alert(
            session,
            "ALERT-PAGE-TIE-TWO",
            "low",
            "WARNING",
            "open",
            timestamp,
        )

    ordered = get_alerts(limit=100, offset=0)
    assert [item["id"] for item in ordered] == [tied_second, tied_first, oldest]
    assert [item["id"] for item in get_alerts(limit=1, offset=1)] == [tied_first]
    assert [item["id"] for item in get_alerts(limit=1, offset=2)] == [oldest]


@pytest.mark.parametrize(
    "params",
    [
        {"offset": -1},
        {"limit": 0},
        {"limit": 101},
    ],
)
def test_alert_pagination_rejects_invalid_parameters(params: dict[str, int]) -> None:
    response = client.get("/alerts", params=params)

    assert response.status_code == 422


def test_get_alert_detail_returns_complete_shape_or_not_found() -> None:
    alert = open_warning("ALERT-DETAIL-01")

    response = client.get(f"/alerts/{alert['id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == alert["id"]
    assert body["acknowledged_at"] is None
    assert body["resolved_at"] is None
    assert client.get("/alerts/999999").status_code == 404


def test_database_rejects_unresolved_duplicate_and_allows_resolved_history() -> None:
    timestamp = datetime(2026, 8, 24, 10, 0, tzinfo=UTC)
    with TestingSessionLocal() as session:
        sensor = make_sensor("ALERT-UNRESOLVED-UNIQUE-01")
        session.add(sensor)
        session.flush()
        first_reading = ReadingModel(
            sensor_id=sensor.id,
            value=5.0,
            unit="C",
            timestamp=timestamp,
        )
        second_reading = ReadingModel(
            sensor_id=sensor.id,
            value=6.0,
            unit="C",
            timestamp=timestamp + timedelta(minutes=1),
        )
        third_reading = ReadingModel(
            sensor_id=sensor.id,
            value=7.0,
            unit="C",
            timestamp=timestamp + timedelta(minutes=2),
        )
        session.add_all([first_reading, second_reading, third_reading])
        session.flush()
        open_alert = AlertModel(
            sensor_id=sensor.id,
            condition="low",
            severity="WARNING",
            status="open",
            origin_reading_id=first_reading.id,
            origin_reading_value=5.0,
            origin_threshold=10.0,
            origin_severity="WARNING",
            last_reading_id=first_reading.id,
            last_reading_value=5.0,
            last_threshold=10.0,
            last_severity="WARNING",
            opened_at=timestamp,
            last_triggered_at=timestamp,
            updated_at=timestamp,
            acknowledged_at=None,
            resolved_at=None,
        )
        session.add(open_alert)
        session.commit()

        acknowledged_duplicate = AlertModel(
            sensor_id=sensor.id,
            condition="low",
            severity="WARNING",
            status="acknowledged",
            origin_reading_id=second_reading.id,
            origin_reading_value=6.0,
            origin_threshold=10.0,
            origin_severity="WARNING",
            last_reading_id=second_reading.id,
            last_reading_value=6.0,
            last_threshold=10.0,
            last_severity="WARNING",
            opened_at=timestamp,
            last_triggered_at=timestamp,
            updated_at=timestamp,
            acknowledged_at=timestamp,
            resolved_at=None,
        )
        session.add(acknowledged_duplicate)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()

        open_alert.status = "resolved"
        open_alert.resolved_at = timestamp + timedelta(minutes=3)
        session.commit()
        new_open_alert = AlertModel(
            sensor_id=sensor.id,
            condition="low",
            severity="WARNING",
            status="open",
            origin_reading_id=third_reading.id,
            origin_reading_value=7.0,
            origin_threshold=10.0,
            origin_severity="WARNING",
            last_reading_id=third_reading.id,
            last_reading_value=7.0,
            last_threshold=10.0,
            last_severity="WARNING",
            opened_at=timestamp + timedelta(minutes=2),
            last_triggered_at=timestamp + timedelta(minutes=2),
            updated_at=timestamp + timedelta(minutes=2),
            acknowledged_at=None,
            resolved_at=None,
        )
        session.add(new_open_alert)
        session.commit()
        assert new_open_alert.id != open_alert.id


class RaceSession:
    def __init__(self, winner: AlertModel) -> None:
        self.winner = winner
        self.pending: list[AlertModel] = []
        self.scalar_calls = 0
        self.rollback_calls = 0
        self.flush_calls = 0

    def scalar(self, statement: object) -> AlertModel | None:
        self.scalar_calls += 1
        if self.scalar_calls == 1:
            return None
        return self.winner

    def add(self, alert: AlertModel) -> None:
        self.pending.append(alert)

    @contextmanager
    def begin_nested(self) -> Generator[None]:
        yield

    def flush(self) -> None:
        self.flush_calls += 1
        if self.flush_calls == 1:
            raise IntegrityError("INSERT alerts", {}, Exception("duplicate"))

    def commit(self) -> None:
        return None

    def rollback(self) -> None:
        self.rollback_calls += 1

    def refresh(self, alert: AlertModel) -> None:
        return None


def test_open_or_update_recovers_from_insert_race_without_losing_reading() -> None:
    timestamp = datetime(2026, 8, 24, 10, 0, tzinfo=UTC)
    winner = AlertModel(
        sensor_id="ALERT-RACE-01",
        condition="low",
        severity="WARNING",
        status="open",
        origin_reading_id=1,
        origin_reading_value=5.0,
        origin_threshold=10.0,
        origin_severity="WARNING",
        last_reading_id=1,
        last_reading_value=5.0,
        last_threshold=10.0,
        last_severity="WARNING",
        opened_at=timestamp,
        last_triggered_at=timestamp,
        updated_at=timestamp,
    )
    session = RaceSession(winner)
    repository = SqlAlchemyAlertRepository(session)  # type: ignore[arg-type]
    persisted_reading = ReadingModel(
        id=2,
        sensor_id="ALERT-RACE-01",
        value=0.0,
        unit="C",
        timestamp=timestamp + timedelta(minutes=1),
    )
    already_persisted = {persisted_reading.id}

    recovered = repository.open_or_update(
        persisted_reading,
        Anomaly(AlertCondition.LOW, AlertSeverity.CRITICAL, 0.0),
    )

    assert persisted_reading.id in already_persisted
    assert recovered is winner
    assert winner.severity == "CRITICAL"
    assert winner.origin_reading_id == 1
    assert winner.last_reading_id == persisted_reading.id
    assert winner.last_severity == "CRITICAL"
    assert session.rollback_calls == 0
