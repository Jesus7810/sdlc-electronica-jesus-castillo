import pytest

from semana5.conversions import celsius_to_fahrenheit, fahrenheit_to_celsius


@pytest.mark.parametrize(
    ("celsius", "expected_fahrenheit"),
    [
        (0, 32),
        (100, 212),
        (-40, -40),
        (25, 77),
    ],
)
def test_celsius_to_fahrenheit(celsius: float, expected_fahrenheit: float) -> None:
    assert celsius_to_fahrenheit(celsius) == expected_fahrenheit


@pytest.mark.parametrize(
    ("fahrenheit", "expected_celsius"),
    [
        (32, 0),
        (212, 100),
        (-40, -40),
        (77, 25),
    ],
)
def test_fahrenheit_to_celsius(fahrenheit: float, expected_celsius: float) -> None:
    assert fahrenheit_to_celsius(fahrenheit) == expected_celsius
