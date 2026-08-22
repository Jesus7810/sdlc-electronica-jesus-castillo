import pytest

from app.domain import (
    AlertCondition,
    AlertSeverity,
    Anomaly,
    classify_anomaly,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (-1.0, Anomaly(AlertCondition.LOW, AlertSeverity.CRITICAL, 0.0)),
        (0.0, Anomaly(AlertCondition.LOW, AlertSeverity.CRITICAL, 0.0)),
        (5.0, Anomaly(AlertCondition.LOW, AlertSeverity.WARNING, 10.0)),
        (9.99, Anomaly(AlertCondition.LOW, AlertSeverity.WARNING, 10.0)),
        (10.0, None),
        (10.01, None),
        (20.0, None),
        (29.99, None),
        (30.0, None),
        (30.01, Anomaly(AlertCondition.HIGH, AlertSeverity.WARNING, 30.0)),
        (35.0, Anomaly(AlertCondition.HIGH, AlertSeverity.WARNING, 30.0)),
        (39.99, Anomaly(AlertCondition.HIGH, AlertSeverity.WARNING, 30.0)),
        (40.0, Anomaly(AlertCondition.HIGH, AlertSeverity.CRITICAL, 40.0)),
        (41.0, Anomaly(AlertCondition.HIGH, AlertSeverity.CRITICAL, 40.0)),
    ],
)
def test_classify_anomaly_applies_operational_threshold_boundaries(
    value: float,
    expected: Anomaly | None,
) -> None:
    anomaly = classify_anomaly(
        value,
        low_critical_threshold=0.0,
        low_warning_threshold=10.0,
        high_warning_threshold=30.0,
        high_critical_threshold=40.0,
    )

    assert anomaly == expected
