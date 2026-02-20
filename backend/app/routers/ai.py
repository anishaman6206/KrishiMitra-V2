# backend/app/routers/ai.py
from __future__ import annotations

from typing import Optional, Dict, Any

from fastapi import APIRouter, Body, HTTPException

from backend.app.services.ai_chat import ask_ai, translate_text
from backend.app.services.soil import resilient_soil_fetcher, get_soil, to_response_dict as soil_to_resp
from backend.app.services.weather import get_weather, to_response_dict as weather_to_resp
from backend.app.services.market import agmarknet_http_fetcher, get_latest_price

router = APIRouter(prefix="/api/ai", tags=["ai"])

@router.post("/ask")
def ai_ask(
    payload: Dict[str, Any] = Body(
        ...,
        example={
            "question": "मेरे धान में पत्ती पीली हो रही है, क्या करूँ?",
            "target_language": "hi",
            "notes": "बारिश पिछले हफ्ते भारी थी",
            "coords": {"lat": 22.57, "lon": 88.36},
            "market": {"district": "Kolkata", "commodity": "Rice", "mandi": "Kolkata"}
        },
    )
):
    """
    Ask AI with optional on-the-fly context.
    Body fields:
      - question (str)                       REQUIRED
      - target_language (str)                OPTIONAL (e.g., "hi", "bn", "en", "mr")
      - notes (str)                          OPTIONAL farmer notes/symptoms
      - coords: {lat, lon}                   OPTIONAL for soil+weather context
      - market: {district, commodity, mandi} OPTIONAL for latest price context
    """
    try:
        q = str(payload.get("question") or "").strip()
        if not q:
            raise HTTPException(status_code=400, detail="question is required")

        target_language = (payload.get("target_language") or "").strip() or None
        notes = (payload.get("notes") or "").strip() or None

        # Optional context build
        ctx_struct: Dict[str, Any] = {}
        coords = payload.get("coords") or {}
        lat = coords.get("lat"); lon = coords.get("lon")
        if lat is not None and lon is not None:
            soil_bundle = get_soil(float(lat), float(lon), resilient_soil_fetcher)
            weather_bundle = get_weather(float(lat), float(lon))
            ctx_struct["soil"] = soil_to_resp(soil_bundle)
            ctx_struct["weather"] = weather_to_resp(weather_bundle)

        market = payload.get("market") or {}
        if market:
            mp = get_latest_price(
                district=market.get("district"),
                commodity=market.get("commodity"),
                mandi=market.get("mandi"),
                fetcher=agmarknet_http_fetcher,
            )
            if mp:
                ctx_struct["price"] = {
                    "commodity": mp.commodity,
                    "price": mp.price,
                    "unit": mp.unit,
                    "mandi": mp.mandi,
                    "district": mp.district,
                    "state": mp.state,
                    "lastUpdated": mp.lastUpdated,
                }

        out = ask_ai(
            question=q,
            target_language=target_language,
            user_context_text=notes,
            context_structured=ctx_struct or None,
        )
        return out
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"ask failed: {e}")

@router.post("/translate")
def ai_translate(
    payload: Dict[str, Any] = Body(
        ...,
        example={"text": "Apply 20 kg urea per acre.", "target_language": "hi"}
    )
):
    """
    Translate arbitrary text using Gemini.
    Body fields:
      - text (str)             REQUIRED
      - target_language (str)  REQUIRED (e.g., "hi", "en", "bn", "mr")
    """
    try:
        text = str(payload.get("text") or "").strip()
        target_language = str(payload.get("target_language") or "").strip()
        if not text or not target_language:
            raise HTTPException(status_code=400, detail="text and target_language are required")

        out = translate_text(text=text, target_language=target_language)
        return out
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"translate failed: {e}")
