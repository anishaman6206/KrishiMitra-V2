# backend/tests/test_farms_router.py
from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

def build_app_sqlite_memory():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, future=True)

    # Create schema for BOTH models
    from backend.app.db import Base
    from backend.app.models.users import User  # noqa: F401
    from backend.app.models.farms import Farm  # noqa: F401
    Base.metadata.create_all(engine)

    # Build app and include routers
    from backend.app.routers.users import router as users_router
    from backend.app.routers.farms import router as farms_router

    app = FastAPI()
    app.include_router(users_router)
    app.include_router(farms_router)

    # Override DB dependency
    from backend.app import db as dbmod
    def _override_get_session():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[dbmod.get_session] = _override_get_session
    return app

def test_register_farm_roundtrip():
    app = build_app_sqlite_memory()
    client = TestClient(app)

    # 1) Create a user
    u = {"name": "Asha", "mobile_number": "+919876543210", "language_pref": "hi"}
    ur = client.post("/api/users/register", json=u)
    assert ur.status_code == 201
    user_id = ur.json()["id"]

    # 2) Create a farm for that user
    f = {
        "user_id": user_id,
        "name": "Asha Farm",
        "area_hectares": 1.25,
        "latitude": 22.5726,
        "longitude": 88.3639,
        "district": "Kolkata",
        "state": "West Bengal",
        "crop_rotation_history": ["rice", "mustard"]
    }
    fr = client.post("/api/farms/register", json=f)
    assert fr.status_code == 201, fr.text
    farm_id = fr.json()["id"]

    # 3) Fetch farm
    fr2 = client.get(f"/api/farms/{farm_id}")
    assert fr2.status_code == 200
    data = fr2.json()
    assert data["name"] == "Asha Farm"
    assert data["district"] == "Kolkata"
    assert data["crop_rotation_history"] == ["rice", "mustard"]

def test_register_farm_user_not_found():
    app = build_app_sqlite_memory()
    client = TestClient(app)

    f = {"user_id": "non-existent", "name": "Ghost Farm"}
    r = client.post("/api/farms/register", json=f)
    assert r.status_code == 404
    assert "User not found" in r.json()["detail"]
