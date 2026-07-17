from sensor_models import Reading, SensorType
from sensor_utils import (
    is_above_threshold,
    to_fahrenheit, 
    round_reading,
    serialize_reading,
    is_same_sensor,
)

#LECTURA 1
reading = Reading(
    sensor_id = 'T1',
    value = 24.6567,
    sensor_type = SensorType.TEMPERATURE,
)

#LECTURA 2
second_reading = Reading(
    sensor_id="T1",
    value=25.1,
    sensor_type=SensorType.TEMPERATURE,
)

#LECTURA 3
third_reading = Reading(
    sensor_id="H1",
    value=60.0,
    sensor_type=SensorType.HUMIDITY,
)

#FUNCION 1 Ver si el valor de la lectura sobrepasa el limite
print('FUNCION 1')
print(reading)
print(is_above_threshold(reading,20.0))
print(is_above_threshold(reading,30.0))

#FUNCION 2 Crear lectura en Fahrenheit
print('FUNCION 2')
fahrenheit_reading = to_fahrenheit(reading)
print(fahrenheit_reading)
print(reading)

#FUNCION 3 Redondear Lectura
print('FUNCION 3')
rounded_reading = round_reading(reading,2)
print(round)
print(reading)

#FUNCION 4 Serializar datos
print('FUNCION 4')
serialized = serialize_reading(reading)
print(serialized)
print(type(serialized))

#FUNCION 5 Comparador de sensores
print('FUNCION 5')
print(is_same_sensor(reading, second_reading))
print(is_same_sensor(reading, third_reading))