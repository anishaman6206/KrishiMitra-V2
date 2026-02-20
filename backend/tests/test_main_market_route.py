# backend/tests/test_main_market_route.py
from __future__ import annotations

from fastapi.testclient import TestClient

def make_app_with_stub_fetcher():
    from backend.app.main import create_app
    from backend.app.routers import market as market_router_mod

    app = create_app()

    # Stub fetcher that returns deterministic rows
    def stub_fetcher(district: str):
        assert district == "Kolkata"
        return [
            {"commodity": "Rice", "unit": "Quintal", "modal_price": "3000", "market": "Kolkata", "district": "Kolkata", "state": "West Bengal", "arrival_date": "2025-10-02"},
            {"commodity": "Jute", "unit": "Quintal", "modal_price": 5000, "market": "Kolkata", "district": "Kolkata", "state": "West Bengal", "arrival_date": "2025-10-02"},
        ]

    # Override the dependency for this test
    app.dependency_overrides[market_router_mod.get_fetcher] = lambda: stub_fetcher
    return app

def test_market_prices_on_real_app():
    app = make_app_with_stub_fetcher()
    client = TestClient(app)

    r = client.get("/api/market/prices", params={"district": "Kolkata"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert len(data) == 2
    assert {x["commodity"] for x in data} == {"Rice", "Jute"}
