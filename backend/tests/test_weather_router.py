# backend/tests/test_weather_router.py
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

def build_app_with_stub():
    from backend.app.routers.weather import router, get_fetcher

    app = FastAPI()
    app.include_router(router)

    def stub_fetcher(lat: float, lon: float):
        assert round(lat, 2) == 22.57 and round(lon, 2) == 88.36
        return {
            "latitude": lat,
            "longitude": lon,
            "current": {"temperature_2m": 31.2, "wind_speed_10m": 3.4, "precipitation": 0.0},
            "daily": {
                "time": ["2025-10-09", "2025-10-10"],
                "temperature_2m_max": [33.0, 34.2],
                "temperature_2m_min": [26.5, 26.7],
                "precipitation_sum": [2.0, 0.0],
            },
        }

    app.dependency_overrides[get_fetcher] = lambda: stub_fetcher
    return app

def test_weather_ok():
    app = build_app_with_stub()
    client = TestClient(app)
    r = client.get("/api/weather", params={"lat": 22.57, "lon": 88.36})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["current"]["temperature_c"] == 31.2
    assert len(data["daily"]) == 2

def test_weather_param_validation():
    app = build_app_with_stub()
    client = TestClient(app)
    r = client.get("/api/weather", params={"lat": 200, "lon": 88.36})  # invalid lat
    assert r.status_code == 422
