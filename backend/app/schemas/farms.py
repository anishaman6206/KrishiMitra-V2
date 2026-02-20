# backend/app/schemas/farms.py
from __future__ import annotations

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class FarmCreate(BaseModel):
    user_id: str = Field(..., min_length=1)
    name: str = Field("My Farm", min_length=1, max_length=200)
    area_hectares: Optional[float] = Field(default=None, ge=0)

    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    district: Optional[str] = None
    state: Optional[str] = None
    preferred_commodities: List[str] = []
    preferred_mandi: Optional[str] = None

    crop_rotation_history: List[str] = Field(default_factory=list)


class FarmUpdate(BaseModel):
    id: str    
    user_id: str = Field(..., min_length=1)
    name: str = Field("My Farm", min_length=1, max_length=200)
    area_hectares: Optional[float] = Field(default=None, ge=0)

    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    district: Optional[str] = None
    state: Optional[str] = None
    preferred_commodities: List[str] = []
    preferred_mandi: Optional[str] = None

    crop_rotation_history: List[str] = Field(default_factory=list)



class FarmOut(BaseModel):
    id: str
    user_id: str
    name: str
    area_hectares: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    district: Optional[str] = None
    state: Optional[str] = None
    preferred_commodities: Optional[List[str]] = None
    preferred_mandi: Optional[str] = None

    crop_rotation_history: List[str]
    created_at: datetime
    updated_at: datetime

    model_config = dict(from_attributes=True)
