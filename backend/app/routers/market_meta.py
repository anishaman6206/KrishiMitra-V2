# backend/app/routers/market_meta.py
from __future__ import annotations
from fastapi import APIRouter, Query
from typing import Dict, List, Optional
from backend.app.services.market_metadata import (
    list_commodities, list_districts, list_markets, list_varieties, list_grades, is_supported
)

router = APIRouter(prefix="/api/market/meta", tags=["market-meta"])

@router.get("/all")
def meta_all() -> Dict[str, List[str]]:
    return {
        "commodities": list_commodities(),
        "districts": list_districts(),
        "mandis": list_markets(),
        "varieties": list_varieties(),
        "grades": list_grades(),
    }

@router.get("/validate")
def meta_validate(
    commodity: Optional[str] = None,
    district: Optional[str] = None,
    mandi: Optional[str] = Query(None, alias="market"),
    variety: Optional[str] = None,
    grade: Optional[str] = None,
) -> Dict[str, bool]:
    return {"ok": is_supported(commodity=commodity, district=district, market=mandi, variety=variety, grade=grade)}
