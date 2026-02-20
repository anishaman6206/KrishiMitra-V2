# backend/tests/test_main_soil_route.py
from __future__ import annotations

from fastapi.testclient import TestClient

def make_app_with_stub_fetcher():
    from backend.app.main import create_app
    from backend.app.routers import soil as soil_router_mod

    app = create_app()

    def stub_fetcher(lat: float, lon: float):
        return {
            "latitude": lat,
            "longitude": lon,
            "properties": {
                "layers": [
                    {"name": "phh2o", "depths": [{"label": "0-5cm", "values": {"mean": 6.5}}]},
                    {"name": "soc", "depths": [{"label": "0-5cm", "values": {"mean": 11.0}}]},
                    {"name": "nitrogen", "depths": [{"label": "0-5cm", "values": {"mean": 1.1}}]},
                ]
            },
        }

    app.dependency_overrides[soil_router_mod.get_fetcher] = lambda: stub_fetcher
    return app

def test_soil_on_real_app():
    app = make_app_with_stub_fetcher()
    client = TestClient(app)
    r = client.get("/api/soil", params={"lat": 22.57, "lon": 88.36})
    assert r.status_code == 200
    assert r.json()["topsoil"]["ph_h2o"] == 6.5
