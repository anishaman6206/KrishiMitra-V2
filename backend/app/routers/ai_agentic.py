# backend/app/routers/ai_agentic.py
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from backend.app.agents.agent_loop import run_agent_once
from backend.app.db import get_session
from sqlalchemy.orm import Session
from backend.app.models.farms import Farm

router = APIRouter(prefix="/api/ai3", tags=["ai-agent"])

class AskAgentic(BaseModel):
    question: str
    target_language: str = "en"
    lat: float | None = None
    lon: float | None = None
    district: str | None = None
    commodity: str | None = None
    mandi: str | None = None
    farm_id: str | None = None   # NEW

@router.post("/ask")
async def ask(req: AskAgentic, db: Session = Depends(get_session)):
    # Load farm prefs if farm_id provided
    prefs = {"preferred_commodities": None, "preferred_mandi": None}
    if req.farm_id:
        farm = db.get(Farm, req.farm_id)
        if farm:
            prefs["preferred_commodities"] = (farm.preferred_commodities or [])[:8]
            prefs["preferred_mandi"] = farm.preferred_mandi

    try:
        out = await run_agent_once(
            req.question,
            target_language=req.target_language,
            lat=req.lat, lon=req.lon,
            district=req.district, commodity=req.commodity, mandi=req.mandi,
            preferred_commodities=prefs["preferred_commodities"],  # NEW
            preferred_mandi=prefs["preferred_mandi"],              # NEW
            max_steps=3,
        )
        return out
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"agent failed: {e}")