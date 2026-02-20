# backend/tests/test_main_weather_route.py
from __future__ import annotations

from fastapi.testclient import TestClient

def make_app_with_stub_fetcher():
    from backend.app.main import create_app
    from backend.app.routers import weather as weather_router_mod

    app = create_app()

    def stub_fetcher(lat: float, lon: float):
        return {
            "latitude": lat, "longitude": lon,
            "current": {"temperature_2m": 29.0, "wind_speed_10m": 2.0, "precipitation": 1.2},
            "daily": {
                "time": ["2025-10-09"],
                "temperature_2m_max": [31.0],
                "temperature_2m_min": [25.0],
                "precipitation_sum": [1.2],
            },
        }

    app.dependency_overrides[weather_router_mod.get_fetcher] = lambda: stub_fetcher
    return app

def test_weather_on_real_app():
    app = make_app_with_stub_fetcher()
    client = TestClient(app)
    r = client.get("/api/weather", params={"lat": 22.57, "lon": 88.36})
    assert r.status_code == 200
    assert r.json()["current"]["temperature_c"] == 29.0
