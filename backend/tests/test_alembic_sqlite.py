# backend/tests/test_alembic_sqlite.py
import os
from pathlib import Path
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import Session

def test_alembic_migration_creates_users_table(tmp_path, monkeypatch):
    # Use a temp SQLite file for this test
    db_path = tmp_path / "km_test.db"
    db_url = f"sqlite:///{db_path.as_posix()}"
    monkeypatch.setenv("KM_DATABASE_URL", db_url)

    # Run alembic upgrade programmatically via subprocess to use your ini/env.py
    import subprocess, sys
    root = Path(__file__).resolve().parents[2]  # repo root
    ini = root / "alembic.ini"
    assert ini.exists(), "alembic.ini not found at repo root"

    # Upgrade
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "-c", str(ini), "upgrade", "head"],
        capture_output=True,
        text=True,
        cwd=str(root),
    )
    assert result.returncode == 0, f"alembic upgrade failed: {result.stderr}"

    # Verify table exists
    engine = create_engine(db_url, future=True)
    insp = inspect(engine)
    assert "users" in insp.get_table_names()

    # Insert & read back using ORM model
    from backend.app.models.users import User
    with Session(engine, future=True) as s:
        s.add(User(name="Ravi", mobile_number="+911234567890", language_pref="en"))
        s.commit()

        row = s.scalar(select(User).where(User.mobile_number == "+911234567890"))
        assert row is not None
        assert row.name == "Ravi"
