# backend/tests/test_db.py
from sqlalchemy import text

def test_session_executes_select_1(monkeypatch):
    # Point DB to in-memory SQLite for this test run
    monkeypatch.setenv("KM_DATABASE_URL", "sqlite+pysqlite:///:memory:")
    monkeypatch.setenv("KM_ENV", "test")
    monkeypatch.setenv("KM_DEBUG", "false")

    # Clear cached settings & engine so overrides take effect
    from backend.app import config as cfg
    from backend.app import db as dbmod
    cfg.get_settings.cache_clear()
    dbmod.get_engine.cache_clear()

    # Now the engine/session should target SQLite
    with dbmod.session_scope() as s:
        result = s.execute(text("SELECT 1"))
        assert result.scalar() == 1
