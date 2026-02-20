# backend/app/routers/recommendations.py
from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Path, Query

from backend.app.services.crop_recommendation import recommend_top3_crops

router = APIRouter(prefix="/api/users", tags=["recommendations"])

@router.get("/{user_id}/recommendations/crop")
def recommend_crops_endpoint(
    user_id: str = Path(..., description="User ID"),
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    rotation_history: Optional[str] = Query(None, description="Comma-separated recent crops"),
) -> List[dict]:
    """
    Returns [{crop, probability}] for top-3 picks. 
    Soil/weather lookups are best-effort (soft-fail). Only LLM failure yields 502.
    """
    try:
        rot_list = [s.strip() for s in (rotation_history or "").split(",") if s.strip()] or None
        return recommend_top3_crops(lat=lat, lon=lon, rotation_history=rot_list)
    except Exception as e:
        # Only fail hard if the LLM or code path truly failed
        raise HTTPException(status_code=502, detail=f"recommendation failed: {e}")
