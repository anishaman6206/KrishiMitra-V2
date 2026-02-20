# backend/tests/test_main_farms_routes.py
from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

def make_sqlite_override_app():
    from backend.app.main import create_app
    from backend.app import db as dbmod
    from backend.app.db import Base
    # Import models so metadata includes them
    from backend.app.models.users import User  # noqa: F401
    from backend.app.models.farms import Farm  # noqa: F401

    # One shared in-memory DB for all connections
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)

    # Create schema
    Base.metadata.create_all(engine)

    # Build the real app (routers already included)
    app = create_app()

    # Override DB dependency with our in-memory session
    def _override_get_session():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[dbmod.get_session] = _override_get_session
    return app

def test_user_then_farm_roundtrip():
    app = make_sqlite_override_app()
    client = TestClient(app)

    # Create user
    u = {"name": "Leela", "mobile_number": "+911112223334", "language_pref": "en"}
    ur = client.post("/api/users/register", json=u)
    assert ur.status_code == 201, ur.text
    user_id = ur.json()["id"]

    # Create farm
    f = {
        "user_id": user_id,
        "name": "Leela Farm",
        "area_hectares": 2.0,
        "latitude": 12.97,
        "longitude": 77.59,
        "district": "Bengaluru Urban",
        "state": "Karnataka",
        "crop_rotation_history": ["ragi", "pulses"]
    }
    fr = client.post("/api/farms/register", json=f)
    assert fr.status_code == 201, fr.text
    farm_id = fr.json()["id"]

    # Read back farm
    r = client.get(f"/api/farms/{farm_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "Leela Farm"
    assert data["district"].startswith("Bengaluru")
