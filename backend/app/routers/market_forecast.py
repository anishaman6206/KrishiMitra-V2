# backend/app/routers/market_forecast.py
from __future__ import annotations

from typing import Optional, Dict
from fastapi import Depends

from fastapi import APIRouter, HTTPException, Query

from backend.app.services.price_forecast import forecast_horizon
from backend.app.services.market import get_latest_price, agmarknet_http_fetcher
from backend.app.models.farms import Farm
from backend.app.db import get_session
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/market", tags=["market-forecast"])

@router.get("/forecast")
def get_price_forecast(
    commodity: str = Query(..., min_length=2),
    # Optional seed; if absent we will fetch the latest current price via Agmarknet
    now_price: Optional[float] = Query(None, gt=0, description="Current modal price in ₹/qtl"),
    horizon_days: int = Query(7, ge=1, le=30, description="Days to forecast"),
    # Filters used to fetch current price when now_price is missing:
    district: Optional[str] = Query(None, description="District name for price lookup"),
    mandi: Optional[str] = Query(None, description="Mandi/market name for price lookup"),
    # Additional metadata (passed to the model encoder if available)
    state: Optional[str] = None,
    variety: Optional[str] = None,
    grade: Optional[str] = None,
):
    """
    Returns calibrated p20/p50/p80 forecasts for the next H days.
    If `now_price` is not provided, we fetch the latest current price
    using the same (district/commodity/mandi) filters.
    """
    try:
        seed_price = now_price
        if seed_price is None:
            mp = get_latest_price(
                district=district,
                commodity=commodity,
                mandi=mandi,
                fetcher=agmarknet_http_fetcher,
            )
            if not mp or not (mp.price == mp.price):  # NaN check
                raise HTTPException(
                    status_code=400,
                    detail="Could not determine current price. Provide `now_price` or refine district/mandi/commodity filters.",
                )
            seed_price = float(mp.price)

        pack = forecast_horizon(
            now_price=seed_price,
            commodity=commodity,
            state=state,
            district=district,
            market=mandi,
            variety=variety,
            grade=grade,
            horizon_days=horizon_days,
        )
        return pack
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"forecast failed: {e}")

@router.get("/forecast/by-farm/{farm_id}")
def forecast_by_farm(farm_id: str, horizon_days: int = 7, db: Session = Depends(get_session)) -> Dict:
    farm = db.get(Farm, farm_id)
    if not farm: raise HTTPException(404, "farm not found")

    out = {}
    for c in (farm.preferred_commodities or [])[:6]:
        try:
            pack = forecast_horizon(
                commodity=c,
                district=farm.district or None,
                mandi=farm.preferred_mandi or None,
                horizon_days=horizon_days,
            )
            out[c] = pack
        except Exception as e:
            out[c] = {"error": str(e)}
    return {"horizon_days": horizon_days, "results": out}