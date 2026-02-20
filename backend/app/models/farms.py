# backend/app/models/farms.py
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Float, ForeignKey, String, func
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db import Base

def _uuid_str() -> str:
    return str(uuid.uuid4())

class Farm(Base):
    """
    A farm owned by a user.
    Minimal fields for MVP: location, area, crop rotation history.
    """
    __tablename__ = "farms"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid_str)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    name: Mapped[str] = mapped_column(String, nullable=False, default="My Farm")
    area_hectares: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    district: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    preferred_commodities: Mapped[list] = mapped_column(SQLITE_JSON, nullable=False, default=list)  # ["Tomato","Potato",...]
    preferred_mandi: Mapped[Optional[str]] = mapped_column(String, nullable=True)                      # optional default mandi

    # Use SQLite JSON for tests; works fine as plain JSON in Postgres via SQLAlchemy
    crop_rotation_history: Mapped[list] = mapped_column(SQLITE_JSON, nullable=False, default=list)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Farm id={self.id} user_id={self.user_id} name={self.name}>"
