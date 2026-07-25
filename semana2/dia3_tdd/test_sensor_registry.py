import pytest
from sensor_registry import SensorNotFoundError, SensorRegistry


def test_get_unknown_sensor_raises() -> None:
    registry = SensorRegistry()
    with pytest.raises(SensorNotFoundError):
        registry.get("GHOST-99")

    
def test_registered_sensor_can_be_retrieved() -> None:
    registry = SensorRegistry()
    sensor = object()
    registry.register("TEMP-01", sensor)
    assert registry.get("TEMP-01") is sensor