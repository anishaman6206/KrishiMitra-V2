# backend/tests/test_weather_service.py
from backend.app.services.weather import (
    normalize_open_meteo,
    get_weather,
    to_response_dict,
    WeatherBundle,
)

def _sample_payload():
    return {
        "latitude": 22.57,
        "longitude": 88.36,
        "current": {
            "temperature_2m": 31.2,
            "wind_speed_10m": 3.4,
            "precipitation": 0.0,
        },
        "daily": {
            "time": ["2025-10-09", "2025-10-10", "2025-10-11"],
            "temperature_2m_max": [33.0, 34.2, 35.1],
            "temperature_2m_min": [26.5, 26.7, 27.0],
            "precipitation_sum": [2.0, 0.0, 5.5],
        },
    }

def test_normalize_open_meteo():
    b = normalize_open_meteo(_sample_payload())
    assert isinstance(b, WeatherBundle)
    assert b.current.temperature_c == 31.2
    assert len(b.daily) == 3
    assert b.daily[0].date == "2025-10-09"
    assert b.daily[0].tmax_c == 33.0

def test_get_weather_with_stub_fetcher():
    def stub_fetcher(lat, lon):
        assert round(lat, 2) == 22.57 and round(lon, 2) == 88.36
        return _sample_payload()

    b = get_weather(22.57, 88.36, stub_fetcher)
    resp = to_response_dict(b)
    assert resp["current"]["temperature_c"] == 31.2
    assert len(resp["daily"]) == 3
