# backend/app/agent/tools.py
from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

# --- Pydantic arg schemas (validation for the agent) ---
class WeatherArgs(BaseModel):
    lat: float
    lon: float

class SoilArgs(BaseModel):
    lat: float
    lon: float

class MarketArgs(BaseModel):
    district: str
    commodity: Optional[str] = None
    mandi: Optional[str] = None

# class RecosArgs(BaseModel):
#     lat: float
#     lon: float

class SatelliteArgs(BaseModel):
    lat: float
    lon: float

class RagArgs(BaseModel):
    query: str
    k: int = 4    


# --- Tool implementations (wrap your existing services) ---
import asyncio

async def _to_thread(func, *args, timeout: float = 15.0, **kwargs):
    return await asyncio.wait_for(asyncio.to_thread(func, *args, **kwargs), timeout=timeout)

# Weather
from backend.app.services.weather import get_weather, to_response_dict as wx_to_dict

async def tool_weather(args: WeatherArgs) -> Dict[str, Any]:
    wb = await _to_thread(get_weather, args.lat, args.lon, timeout=15.0)
    return wx_to_dict(wb)

# Soil
from backend.app.services.soil import resilient_soil_fetcher, get_soil, to_response_dict as soil_to_dict

async def tool_soil(args: SoilArgs) -> Dict[str, Any]:
    # quick retry 2x
    for i in range(2):
        try:
            raw = await _to_thread(resilient_soil_fetcher, args.lat, args.lon, timeout=10.0)
            bundle = get_soil(args.lat, args.lon, lambda _a, _b: raw)
            return soil_to_dict(bundle)
        except Exception:
            if i == 1:
                raise
            await asyncio.sleep(0.25 * (i + 1))

# Market
from backend.app.services.market import fetch_prices, agmarknet_http_fetcher

async def tool_market(args: MarketArgs) -> List[Dict[str, Any]]:
    rows = await _to_thread(
        fetch_prices,
        district=args.district,
        commodity=args.commodity,
        mandi=args.mandi,
        fetcher=agmarknet_http_fetcher,
        timeout=12.0,
    )
    return [r.__dict__ for r in rows][:25]

# Crop Recommendations (Gemini)
from backend.app.services.crop_recommendation import recommend_top3_crops

# async def tool_recos(args: RecosArgs) -> List[Dict[str, Any]]:
#     return await _to_thread(recommend_top3_crops, lat=args.lat, lon=args.lon, rotation_history=None, timeout=12.0)

# Satellite (optional)
import os
from backend.app.services.satellite import sentinel_summary
SATELLITE_ENABLED = bool(os.getenv("SH_CLIENT_ID") and os.getenv("SH_CLIENT_SECRET"))

async def tool_satellite(args: SatelliteArgs) -> Dict[str, Any]:
    if not SATELLITE_ENABLED:
        return {"error": "satellite disabled"}
    return await asyncio.wait_for(sentinel_summary(args.lat, args.lon, aoi_m=300, days=45, res=10), timeout=15.0)

from backend.app.rag.retrieve import retrieve as rag_retrieve
async def tool_rag(args: RagArgs) -> List[Dict[str, Any]]:
    """
    Returns compact hits: [{score, title, source, page, snippet}]
    (We shorten text to a snippet to keep LLM context lean.)
    """
    hits = await _to_thread(rag_retrieve, args.query, args.k, timeout=12.0)
    out: List[Dict[str, Any]] = []
    for h in hits:
        txt = h.get("text") or ""
        snippet = (txt[:400] + "…") if len(txt) > 400 else txt
        out.append({
            "score": h.get("score"),
            "title": h.get("title"),
            "source": h.get("source"),
            "page": h.get("page"),
            "snippet": snippet,
        })
    return out

# --- Tool registry for planner help text ---
TOOL_DESCRIPTIONS = {
    "weather": "Get current + 7-day forecast with rainfall (requires: lat, lon).",
    "soil": "Get topsoil pH, SOC, N, texture (requires: lat, lon).",
    "market": "Get current prices by district (optional: commodity, mandi).",
    # "recos": "Get top-3 crop recommendations (requires: lat, lon).",
    "satellite": "Get NDVI/NDMI/NDWI/LAI summary (requires: lat, lon; credentials needed).",
    "rag": "Retrieve policy/guidelines or generic knowledge from local documents (query, k).",  # NEW
}
