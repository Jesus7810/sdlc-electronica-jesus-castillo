from semana0.hola_sensor import Sensor
 
def test_sensor_reads_value():
    assert Sensor("TEMP-01").read() == 23.5