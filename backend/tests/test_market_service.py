# backend/tests/test_market_service.py
from backend.app.services.market import (
    normalize_agmarknet_rows,
    fetch_prices_for_district,
    MarketPrice,
)

def test_normalize_agmarknet_rows_basic():
    rows = [
        {
            "commodity": "Wheat",
            "unit": "Quintal",
            "modal_price": "2250",
            "market": "Azadpur",
            "district": "Delhi",
            "state": "Delhi",
            "arrival_date": "2025-10-01",
        },
        {
            "commodity": "Potato",
            "unit": "Quintal",
            "modal_price": 1400,
            "market": "Howrah",
            "district": "Howrah",
            "state": "West Bengal",
            "arrival_date": "2025-10-01",
        },
    ]
    res = normalize_agmarknet_rows(rows)
    assert len(res) == 2
    assert isinstance(res[0], MarketPrice)
    names = {r.commodity for r in res}
    assert names == {"Wheat", "Potato"}
    # price parsing
    wheat = next(r for r in res if r.commodity == "Wheat")
    assert wheat.price == 2250.0
    assert wheat.mandi == "Azadpur"

def test_fetch_prices_for_district_with_stub():
    # stub fetcher returns two rows for any district
    def stub_fetcher(d: str):
        assert d == "Kolkata"
        return [
            {"commodity": "Rice", "unit": "Quintal", "modal_price": "3000", "market": "Kolkata", "district": "Kolkata", "state": "West Bengal", "arrival_date": "2025-10-02"},
            {"commodity": "Jute", "unit": "Quintal", "modal_price": 5000, "market": "Kolkata", "district": "Kolkata", "state": "West Bengal", "arrival_date": "2025-10-02"},
        ]

    out = fetch_prices_for_district("Kolkata", stub_fetcher)
    assert len(out) == 2
    assert {r.commodity for r in out} == {"Rice", "Jute"}
    assert all(r.district == "Kolkata" for r in out)
