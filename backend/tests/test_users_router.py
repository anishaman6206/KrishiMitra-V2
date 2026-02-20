# backend/tests/test_users_router.py
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

def build_app_sqlite_memory():
    # Create ONE shared in-memory SQLite "database" for all connections
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # <- critical so all sessions share the same memory DB
    )
    SessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        future=True,
    )

    # Import models and create schema on this engine
    from backend.app.db import Base
    from backend.app.models.users import User  # noqa: F401
    Base.metadata.create_all(engine)

    # Build a throwaway FastAPI app and include the users router
    from backend.app.routers.users import router
    app = FastAPI()
    app.include_router(router)

    # Override get_session dependency to use our shared in-memory DB
    from backend.app import db as dbmod

    def _override_get_session():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[dbmod.get_session] = _override_get_session
    return app

def test_register_and_profile_roundtrip():
    app = build_app_sqlite_memory()
    client = TestClient(app)

    payload = {"name": "Asha", "mobile_number": "+919876543210", "language_pref": "hi"}
    r = client.post("/api/users/register", json=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    user_id = data["id"]

    r2 = client.get(f"/api/users/{user_id}/profile")
    assert r2.status_code == 200
    prof = r2.json()
    assert prof["id"] == user_id
    assert prof["language_pref"] == "hi"

def test_register_duplicate_conflict():
    app = build_app_sqlite_memory()
    client = TestClient(app)

    payload = {"name": "Dup1", "mobile_number": "+911234567890", "language_pref": "en"}
    r1 = client.post("/api/users/register", json=payload)
    assert r1.status_code == 201

    payload2 = {"name": "Dup2", "mobile_number": "+911234567890", "language_pref": "en"}
    r2 = client.post("/api/users/register", json=payload2)
    assert r2.status_code == 409
    assert "already exists" in r2.json()["detail"]
