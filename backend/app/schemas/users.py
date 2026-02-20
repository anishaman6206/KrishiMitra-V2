# backend/app/schemas/users.py
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ----- Input Schemas -----
class UserCreate(BaseModel):
    """
    Payload to register a new user.
    """
    name: str = Field(..., min_length=1, max_length=200)
    mobile_number: str = Field(..., min_length=5, max_length=30)
    language_pref: Optional[str] = Field(default="en", min_length=2, max_length=5)


# ----- Output Schemas -----
class UserOut(BaseModel):
    id: str
    name: str
    mobile_number: str
    language_pref: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = dict(from_attributes=True)  # allow ORM objects
