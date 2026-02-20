# backend/tests/test_main_users_routes.py
from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

def make_sqlite_override_app():
    # Import app factory and db bits
    from backend.app.main import create_app
    from backend.app import db as dbmod
    from backend.app.db import Base
    from backend.app.models.users import User  # noqa: F401

    # Shared in-memory DB for all sessions
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)

    # Create schema
    Base.metadata.create_all(engine)

    # Build the real app (which already includes routers)
    app = create_app()

    # Override get_session dependency with our in-memory session
    def _override_get_session():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[dbmod.get_session] = _override_get_session
    return app

def test_register_and_profile_on_real_app():
    app = make_sqlite_override_app()
    client = TestClient(app)

    payload = {"name": "Leela", "mobile_number": "+911112223334", "language_pref": "en"}
    r = client.post("/api/users/register", json=payload)
    assert r.status_code == 201, r.text
    uid = r.json()["id"]

    r2 = client.get(f"/api/users/{uid}/profile")
    assert r2.status_code == 200
    assert r2.json()["mobile_number"].endswith("3334")
