# backend/app/routers/market.py
from __future__ import annotations

from dataclasses import asdict
from typing import Callable, List, Sequence, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.app.services.market import (
    MarketPrice,
    fetch_prices,
    agmarknet_http_fetcher,
)
from sqlalchemy.orm import Session
from backend.app.models.farms import Farm
from backend.app.db import get_session

router = APIRouter(prefix="/api/market", tags=["market"])

FetchFunc = Callable[[Optional[str], Optional[str], Optional[str]], Sequence[Dict]]

def get_fetcher() -> FetchFunc:
    return agmarknet_http_fetcher

@router.get("/prices")
def get_market_prices(
    district: Optional[str] = Query(None, min_length=2, description="District name, e.g., 'Kolkata'"),
    commodity: Optional[str] = Query(None, description="Commodity filter, e.g., 'Wheat'"),
    mandi: Optional[str] = Query(None, description="Mandi/market filter, e.g., 'Azadpur'"),
    fetcher: FetchFunc = Depends(get_fetcher),
) -> List[dict]:
    """
    Return normalized market prices for optional filters.
    If no filters are provided, returns a small recent sample (server limit applies).
    """
    try:
        prices: List[MarketPrice] = fetch_prices(district=district, commodity=commodity, mandi=mandi, fetcher=fetcher)
        return [asdict(p) for p in prices]
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"market fetch failed: {e}")

@router.get("/prices/by-farm/{farm_id}")
def prices_by_farm(farm_id: str, db: Session = Depends(get_session)) -> Dict:
    farm = db.get(Farm, farm_id)
    if not farm: raise HTTPException(404, "farm not found")
    if not farm.district: raise HTTPException(400, "farm has no district set")

    results = {}
    for c in (farm.preferred_commodities or [])[:8]:  # cap for speed
        rows = fetch_prices(
            district=farm.district,
            commodity=c,
            mandi=farm.preferred_mandi,
            fetcher=agmarknet_http_fetcher,
        )
        results[c] = [r.__dict__ for r in rows]
    return {
        "district": farm.district,
        "preferred_mandi": farm.preferred_mandi,
        "results": results,
    }