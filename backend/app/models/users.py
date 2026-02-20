# backend/app/models/users.py
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db import Base


def _uuid_str() -> str:
    return str(uuid.uuid4())


class User(Base):
    """
    Minimal user record for KrishiMitra.
    - `id`: UUID string primary key
    - `mobile_number`: unique identifier for users (E.164 preferred, but not enforced here)
    - `language_pref`: UI/response language hint (e.g., 'en', 'hi', 'bn')
    """
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(primary_key=True, default=_uuid_str)
    name: Mapped[str] = mapped_column(nullable=False)
    mobile_number: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)

    language_pref: Mapped[Optional[str]] = mapped_column(default="en", nullable=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User id={self.id} mobile={self.mobile_number}>"
