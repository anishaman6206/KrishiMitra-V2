# backend/tests/test_users_model.py
from sqlalchemy import text, select
from sqlalchemy.exc import IntegrityError

def test_users_table_create_insert_roundtrip(monkeypatch):
    # Use in-memory SQLite for this test
    monkeypatch.setenv("KM_DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("KM_ENV", "test")
    monkeypatch.setenv("KM_DEBUG", "false")

    # Clear caches so overrides take effect
    from backend.app import config as cfg
    from backend.app import db as dbmod
    cfg.get_settings.cache_clear()
    dbmod.get_engine.cache_clear()

    # Import model so SQLAlchemy registers the table on Base.metadata
    from backend.app.models.users import User
    from backend.app.db import Base, session_scope, get_engine

    # Create tables
    Base.metadata.create_all(get_engine())

    # Insert one user
    with session_scope() as s:
        u = User(name="Asha", mobile_number="+919876543210", language_pref="hi")
        s.add(u)

    # Verify with a round-trip query
    with session_scope() as s:
        row = s.scalar(select(User).where(User.mobile_number == "+919876543210"))
        assert row is not None
        assert row.name == "Asha"
        assert row.language_pref == "hi"

    # Unique constraint check on mobile_number
    with session_scope() as s:
        s.add(User(name="Dup", mobile_number="+919876543210"))
        try:
            s.flush()
            assert False, "Expected IntegrityError on duplicate mobile_number"
        except IntegrityError:
            s.rollback()

    # Sanity: table exists
    with session_scope() as s:
        exists = s.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        ).fetchone()
        assert exists is not None
