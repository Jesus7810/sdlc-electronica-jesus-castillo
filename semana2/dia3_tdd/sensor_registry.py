class SensorNotFoundError(Exception):
    pass


class SensorRegistry:
    def __init__(self) -> None:
        self._sensors: dict[str, object] = {}

    def register(self, sensor_id: str, sensor: object) -> None:
        self._sensors[sensor_id] = sensor

    def get(self, sensor_id: str) -> object:
        if sensor_id in self._sensors:
            return self._sensors[sensor_id]

        raise SensorNotFoundError(sensor_id)