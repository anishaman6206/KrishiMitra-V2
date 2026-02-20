# backend/app/routers/users.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db import get_session
from backend.app.models.users import User
from backend.app.schemas.users import UserCreate, UserOut

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: Session = Depends(get_session)) -> UserOut:
    """
    Create a new user if the mobile number isn't already registered.
    """
    # Check for existing user by mobile
    exists = db.scalar(select(User).where(User.mobile_number == payload.mobile_number))
    if exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this mobile number already exists.",
        )

    u = User(
        name=payload.name,
        mobile_number=payload.mobile_number,
        language_pref=payload.language_pref,
    )
    db.add(u)
    db.flush()  # get generated PKs before commit for response
    db.commit()
    db.refresh(u)
    return u


@router.get("/{user_id}/profile", response_model=UserOut)
def get_profile(user_id: str, db: Session = Depends(get_session)) -> UserOut:
    """
    Return a user's profile by id.
    """
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return u
