# backend/app/routers/farms.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from backend.app.db import get_session
from backend.app.models.users import User
from backend.app.models.farms import Farm
from backend.app.schemas.farms import FarmCreate, FarmOut

class PrefsUpdate(BaseModel):
    preferred_commodities: List[str] = []
    preferred_mandi: Optional[str] = None

router = APIRouter(prefix="/api/farms", tags=["farms"])

@router.post("/register", response_model=FarmOut, status_code=status.HTTP_201_CREATED)
def register_farm(payload: FarmCreate, db: Session = Depends(get_session)) -> FarmOut:
    """
    Create a farm for a given user_id. Fails if user doesn't exist.
    """
    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    farm = Farm(
        user_id=payload.user_id,
        name=payload.name,
        area_hectares=payload.area_hectares,
        latitude=payload.latitude,
        longitude=payload.longitude,
        district=payload.district,
        state=payload.state,
        crop_rotation_history=payload.crop_rotation_history or [],
    )
    db.add(farm)
    db.flush()
    db.commit()
    db.refresh(farm)
    return farm

@router.get("/{farm_id}", response_model=FarmOut)
def get_farm(farm_id: str, db: Session = Depends(get_session)) -> FarmOut:
    farm = db.get(Farm, farm_id)
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found.")
    return farm

@router.get("/{farm_id}/preferences")
def get_farm_preferences(farm_id: str, db: Session = Depends(get_session)):
    farm = db.get(Farm, farm_id)
    if not farm: raise HTTPException(404, "farm not found")
    return {
        "preferred_commodities": farm.preferred_commodities or [],
        "preferred_mandi": farm.preferred_mandi,
        "district": farm.district,
        "state": farm.state,
    }

@router.put("/{farm_id}/preferences")
def update_farm_preferences(farm_id: str, req: PrefsUpdate, db: Session = Depends(get_session)):
    farm = db.get(Farm, farm_id)
    if not farm: raise HTTPException(404, "farm not found")
    # Optional: validate against encoder.json
    from backend.app.services.market_metadata import is_supported
    valid = [c for c in (req.preferred_commodities or []) if is_supported(commodity=c)]
    farm.preferred_commodities = valid
    farm.preferred_mandi = req.preferred_mandi
    db.add(farm); db.commit(); db.refresh(farm)
    return {"ok": True}