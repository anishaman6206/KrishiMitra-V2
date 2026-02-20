# backend/tests/test_market_router.py
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

def build_app_with_stub():
    # Import inside to ensure test isolation
    from backend.app.routers.market import router, get_fetcher

    app = FastAPI()
    app.include_router(router)

    # Stub: returns two rows regardless of district
    def stub_fetcher(district: str):
        assert district == "Kolkata"
        return [
            {
                "commodity": "Rice",
                "unit": "Quintal",
                "modal_price": "3000",
                "market": "Kolkata",
                "district": "Kolkata",
                "state": "West Bengal",
                "arrival_date": "2025-10-02",
            },
            {
                "commodity": "Jute",
                "unit": "Quintal",
                "modal_price": 5000,
                "market": "Kolkata",
                "district": "Kolkata",
                "state": "West Bengal",
                "arrival_date": "2025-10-02",
            },
        ]

    # Override the fetcher dependency with our stub
    app.dependency_overrides[get_fetcher] = lambda: stub_fetcher
    return app

def test_get_market_prices_ok():
    app = build_app_with_stub()
    client = TestClient(app)

    r = client.get("/api/market/prices", params={"district": "Kolkata"})
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 2
    commodities = {d["commodity"] for d in data}
    assert commodities == {"Rice", "Jute"}
    # shape check
    assert {"commodity","unit","price","mandi","district","state","lastUpdated"} <= set(data[0].keys())

def test_get_market_prices_missing_param():
    app = build_app_with_stub()
    client = TestClient(app)

    r = client.get("/api/market/prices")  # no district
    # FastAPI will 422 for missing required query parameter
    assert r.status_code == 422
