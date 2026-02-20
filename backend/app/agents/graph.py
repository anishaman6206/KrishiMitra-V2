from __future__ import annotations
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from langgraph.graph import StateGraph, END
import asyncio

# Existing services (unchanged)
from backend.app.services.weather import (
    get_weather, to_response_dict as wx_to_dict
)
from backend.app.services.soil import (
    resilient_soil_fetcher, get_soil, to_response_dict as soil_to_dict
)
from backend.app.services.market import (
    fetch_prices, agmarknet_http_fetcher
)
from backend.app.services.crop_recommendation import (
    recommend_top3_crops, _gemini_call as gemini_call
)
from backend.app.services.satellite import sentinel_summary  # NEW location

class AskState(BaseModel):
    question: str
    target_language: str = "en"
    lat: Optional[float] = None
    lon: Optional[float] = None
    district: Optional[str] = None
    commodity: Optional[str] = None
    mandi: Optional[str] = None

    weather: Optional[Dict[str, Any]] = None
    wx24: Optional[Dict[str, Any]] = None
    soil: Optional[Dict[str, Any]] = None
    prices: Optional[List[Dict[str, Any]]] = None
    recos: Optional[List[Dict[str, Any]]] = None
    sat: Optional[Dict[str, Any]] = None

    answer: Optional[str] = None
    error: Optional[str] = None

async def _to_thread(func, *args, timeout: float = 20.0, **kwargs):
    return await asyncio.wait_for(asyncio.to_thread(func, *args, **kwargs), timeout=timeout)

async def _soil_with_retry(lat: float, lon: float, tries: int = 3, per_try_timeout: float = 12.0):
    for i in range(1, tries + 1):
        try:
            raw = await _to_thread(resilient_soil_fetcher, lat, lon, timeout=per_try_timeout)
            bundle = get_soil(lat, lon, lambda _a, _b: raw)
            return soil_to_dict(bundle)
        except Exception:
            if i == tries:
                return None
            await asyncio.sleep(0.2 * i)

GATHER_TIMEOUT_S = 25.0

async def node_gather(state: AskState) -> AskState:
    tasks = []

    async def t_weather():
        if state.lat is None or state.lon is None: return
        try:
            wb = await _to_thread(get_weather, state.lat, state.lon, timeout=25.0)
            state.weather = wx_to_dict(wb)  # includes next24h_total_rain_mm when available
        except Exception:
            state.weather = None

  

    async def t_soil():
        if state.lat is None or state.lon is None: return
        state.soil = await _soil_with_retry(state.lat, state.lon)

    async def t_market():
        if not state.district: return
        try:
            rows = await _to_thread(
                fetch_prices,
                district=state.district,
                commodity=state.commodity,
                mandi=state.mandi,
                fetcher=agmarknet_http_fetcher,
                timeout=GATHER_TIMEOUT_S,
            )
            state.prices = [r.__dict__ for r in rows][:25]
        except Exception:
            state.prices = None

    async def t_recos():
        if state.lat is None or state.lon is None: return
        try:
            state.recos = await _to_thread(recommend_top3_crops, lat=state.lat, lon=state.lon, rotation_history=None, timeout=GATHER_TIMEOUT_S)
        except Exception:
            state.recos = None

    async def t_sat():
        if state.lat is None or state.lon is None: return
        try:
            state.sat = await asyncio.wait_for(sentinel_summary(state.lat, state.lon, aoi_m=300, days=45, res=10), timeout=35.0)
        except Exception:
            state.sat = None

    tasks.extend([t_weather(), t_soil(), t_market(), t_recos(), t_sat()])
    await asyncio.gather(*tasks, return_exceptions=True)
    return state

async def node_llm(state: AskState) -> AskState:
    try:
        pieces = []
        if state.weather:
            pieces.append(f"Weather(now): {state.weather.get('current')}")
            if state.weather.get("daily"):
                d0 = state.weather["daily"][0]
                rain0 = d0.get("rain_mm", d0.get("precip_mm"))
                pieces.append(f"Weather(day1): tmax={d0.get('tmax_c')} tmin={d0.get('tmin_c')} rain={rain0}mm RH={d0.get('humidity_mean_pct')}")
        if state.wx24:
            pieces.append(f"Rain next 24h: {state.wx24.get('total_rain_next_24h_mm')} mm (max wind {state.wx24.get('max_wind_next_24h_kmh')} km/h)")
        if state.soil and state.soil.get("topsoil"):
            pieces.append(f"Soil(top): {state.soil['topsoil']}")
        if state.sat:
            pieces.append(f"Satellite: NDVI={state.sat.get('ndvi_mean')} NDMI={state.sat.get('ndmi_mean')} NDWI={state.sat.get('ndwi_mean')} LAI={state.sat.get('lai_mean')} ({state.sat.get('reliability')})")
        if state.prices:
            sample = [f"{p['commodity']}:{p['price']}" for p in state.prices[:5]]
            pieces.append(f"Market: {sample}")
        if state.recos:
            pieces.append(f"Top crops: {state.recos}")

        prompt = f"""You are KrishiMitra. Answer the farmer's question concisely.
Question: {state.question}

Context (JSON-like):
{pieces}

Rules:
- Prefer rainfall (next 24h and daily rain_mm) when reasoning about water availability.
- If some signals are missing, state assumptions briefly.
Respond in {state.target_language}.
"""
        text = await _to_thread(gemini_call, prompt, timeout=45.0)
        state.answer = text
    except Exception as e:
        state.error = f"llm failed: {e}"
    return state

graph = StateGraph(AskState)
graph.add_node("gather", node_gather)
graph.add_node("llm", node_llm)
graph.set_entry_point("gather")
graph.add_edge("gather", "llm")
graph.add_edge("llm", END)

ASK_GRAPH = graph.compile()
