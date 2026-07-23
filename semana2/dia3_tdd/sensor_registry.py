class SensorNotFoundError(Exception):
    pass


class SensorRegistry:
    def __init__(self) -> None:
        self._sensors: dict[str, object] = {}

    def register(self, sensor_id: str, sensor: object) -> None:
        self._sensors[sensor_id] = sensor

    def get(self, sensor_id: str) -> object:
        self._validate_sensor_exists(sensor_id)
        return self._sensors[sensor_id]

    def _validate_sensor_exists(self, sensor_id: str) -> None:
        if sensor_id not in self._sensors:
            raise SensorNotFoundError(sensor_id)