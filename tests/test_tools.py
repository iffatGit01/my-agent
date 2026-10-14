"""Plain pytest unit tests for the tool functions (no browser needed)."""

from agent_app.tools import add_numbers, get_weather


def test_get_weather_known_city():
    assert "Dhaka" in get_weather("dhaka")


def test_get_weather_unknown_city():
    assert "no weather data" in get_weather("Atlantis")


def test_add_numbers():
    assert add_numbers(2, 40) == 42
