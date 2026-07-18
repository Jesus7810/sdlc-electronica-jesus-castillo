from uart_driver.parsers import ModbusParser, NMEAParser


def test_modbus_accepts_valid_frame() -> None:
    """Debe aceptar un frame Modbus válido."""
    parser = ModbusParser()
    frame = bytes([1, 3, 25])
    assert parser.can_parse(frame) is True


def test_modbus_rejects_invalid_frame() -> None:
    """Debe rechazar un frame Modbus demasiado corto."""
    parser = ModbusParser()
    frame = bytes([1, 3])
    assert parser.can_parse(frame) is False


def test_modbus_parses_frame() -> None:
    """Debe convertir el frame Modbus en un diccionario."""
    parser = ModbusParser()
    frame = bytes([1, 3, 25])
    result = parser.parse(frame)
    assert result["address"] == 1
    assert result["function"] == 3
    assert result["data"] == [25]


def test_nmea_accepts_gpgga_sentence() -> None:
    """Debe aceptar una sentencia GPGGA."""
    parser = NMEAParser()
    sentence = "$GPGGA,123519,1907.000,N,09655.000,W"
    assert parser.can_parse(sentence) is True


def test_nmea_rejects_other_sentence() -> None:
    """Debe rechazar una sentencia que no sea GPGGA."""
    parser = NMEAParser()
    sentence = "$GPRMC,123519,1907.000,N,09655.000,W"
    assert parser.can_parse(sentence) is False


def test_nmea_parses_sentence() -> None:
    """Debe extraer datos básicos de una sentencia GPGGA."""
    parser = NMEAParser()
    sentence = "$GPGGA,123519,1907.000,N,09655.000,W"
    result = parser.parse(sentence)
    assert result["time"] == "123519"
    assert result["latitude"] == "1907.000"
    assert result["longitude"] == "09655.000"