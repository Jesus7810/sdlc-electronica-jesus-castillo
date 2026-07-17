from sensor_models import Reading, SensorType
from dataclasses import replace

#FUNCION 1
def is_above_threshold(reading: Reading, threshold: float) -> bool:
    return reading.value > threshold

#FUNCION 2
def to_fahrenheit(reading: Reading) -> Reading:
    if reading.sensor_type != SensorType.TEMPERATURE:
        raise ValueError(
            'to_fahrenheit solo acepta lecturas de temperatura'
        )
    
    fahrenheit = reading.value * 9/5 + 32

    return replace(reading, value = fahrenheit)

#FUNCION 3
def round_reading(reading: Reading, digits: int) -> Reading:
    return replace(reading, value = round(reading.value,digits))

#FUNCION 4
def serialize_reading(reading: Reading) -> bytes:
    frame = (
        f"{reading.sensor_id}:"
        f"{reading.sensor_type.name}:"
        f"{reading.value:.2f}"
    )
    return frame.encode()

#FUNCION 5
def is_same_sensor(first: Reading, second: Reading) -> bool:
    return first.sensor_id == second.sensor_id