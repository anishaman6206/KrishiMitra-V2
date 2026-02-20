# backend/tests/test_soil_router.py
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

def build_app_with_stub():
    from backend.app.routers.soil import router, get_fetcher

    app = FastAPI()
    app.include_router(router)

    def stub_fetcher(lat: float, lon: float):
        assert round(lat, 2) == 22.57 and round(lon, 2) == 88.36
        return {
            "latitude": lat,
            "longitude": lon,
            "properties": {
                "layers": [
                    {"name": "phh2o", "depths": [
                        {"label": "0-5cm", "values": {"mean": 6.8}},
                        {"label": "5-15cm", "values": {"mean": 6.6}},
                    ]},
                    {"name": "soc", "depths": [
                        {"label": "0-5cm", "values": {"mean": 12.0}},
                        {"label": "5-15cm", "values": {"mean": 10.5}},
                    ]},
                    {"name": "nitrogen", "depths": [
                        {"label": "0-5cm", "values": {"mean": 1.2}},
                        {"label": "5-15cm", "values": {"mean": 1.0}},
                    ]},
                ]
            },
        }

    app.dependency_overrides[get_fetcher] = lambda: stub_fetcher
    return app

def test_soil_ok():
    app = build_app_with_stub()
    client = TestClient(app)
    r = client.get("/api/soil", params={"lat": 22.57, "lon": 88.36})
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["topsoil"]["ph_h2o"] == 6.8
    assert len(data["layers"]) == 2

def test_soil_param_validation():
    app = build_app_with_stub()
    client = TestClient(app)
    r = client.get("/api/soil", params={"lat": 200, "lon": 88.36})  # invalid
    assert r.status_code == 422
