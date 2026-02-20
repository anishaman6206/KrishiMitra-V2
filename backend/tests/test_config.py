# backend/tests/test_config.py
def test_settings_defaults():
    from backend.app.config import get_settings
    s = get_settings()
    assert s.env == "dev"
    assert isinstance(s.debug, bool)
    assert s.database_url.startswith("postgresql+psycopg://")
    assert isinstance(s.cors_origins, list)
    assert len(s.cors_origins) >= 1


def test_env_overrides(monkeypatch):
    # Override via env vars
    monkeypatch.setenv("KM_ENV", "prod")
    monkeypatch.setenv("KM_DEBUG", "false")
    monkeypatch.setenv(
        "KM_CORS_ORIGINS",
        "https://app.example.com, https://admin.example.com",
    )
    monkeypatch.setenv(
        "KM_DATABASE_URL",
        "postgresql+psycopg://user:pass@db:5432/prod_db",
    )

    # Clear the LRU cache so new env vars are read
    from backend.app import config as cfg
    cfg.get_settings.cache_clear()

    s = cfg.get_settings()
    assert s.env == "prod"
    assert s.debug is False
    assert s.cors_origins == [
        "https://app.example.com",
        "https://admin.example.com",
    ]
    assert s.database_url.endswith("/prod_db")
