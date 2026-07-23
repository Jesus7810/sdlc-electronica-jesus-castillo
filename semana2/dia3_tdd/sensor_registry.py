class SensorNotFoundError(Exception):
    pass


class SensorRegistry:
    def get(self, sensor_id: str) -> None:
        raise SensorNotFoundError(sensor_id)