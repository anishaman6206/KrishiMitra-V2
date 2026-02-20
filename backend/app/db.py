# backend/app/db.py
from __future__ import annotations

from contextlib import contextmanager
from functools import lru_cache
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from .config import get_settings

Base = declarative_base()
s = get_settings()
engine = create_engine(
    s.database_url, connect_args={"check_same_thread": False} # works for multi threading
)

@lru_cache
def get_engine() -> Engine:
    """
    Lazily create and cache the SQLAlchemy engine using the current settings.
    Cache is cleared in tests when env vars change.
    """
    s = get_settings()
    # echo=s.debug will log SQL in dev
    engine = create_engine(
        s.database_url,
        pool_pre_ping=True,
        echo=s.debug and s.env == "dev",
        future=True,
    )
    return engine


def _session_factory() -> sessionmaker[Session]:
    """Internal session factory bound to the (cached) engine."""
    return sessionmaker(bind=get_engine(), autoflush=False, autocommit=False, expire_on_commit=False, future=True)


def get_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency style: `Depends(get_session)`.
    Yields a session and ensures it's closed after the request.
    """
    SessionLocal = _session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """
    Handy context manager for scripts/tests:

        from backend.app.db import session_scope
        with session_scope() as s:
            s.execute(text("SELECT 1"))
    """
    SessionLocal = _session_factory()
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
