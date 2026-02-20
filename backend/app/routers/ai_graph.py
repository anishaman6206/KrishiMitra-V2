# backend/app/routers/ai_graph.py
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.app.agents.graph import ASK_GRAPH, AskState

router = APIRouter(prefix="/api/ai2", tags=["ai-graph"])

class AskRequest(BaseModel):
    question: str
    target_language: str = "en"
    lat: float | None = None
    lon: float | None = None
    district: str | None = None
    commodity: str | None = None
    mandi: str | None = None

@router.post("/ask")
async def ask_ai(req: AskRequest):
    try:
        # Send a plain dict in, get a dict out
        init_state = AskState(**req.model_dump()).model_dump()
        result: dict = await ASK_GRAPH.ainvoke(init_state)

        # guard on error (dict access)
        if result.get("error"):
            raise HTTPException(status_code=502, detail=result["error"])

        return {
            "answer": result.get("answer"),
            "used": {
                "has_weather": bool(result.get("weather")),
                "has_soil": bool(result.get("soil")),
                "has_prices": bool(result.get("prices")),
                "has_recos": bool(result.get("recos")),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"graph failed: {e}")
