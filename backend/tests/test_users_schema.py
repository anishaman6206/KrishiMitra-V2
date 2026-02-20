# backend/tests/test_users_schema.py
import pytest
from datetime import datetime, timedelta
from backend.app.schemas.users import UserCreate, UserOut

def test_user_create_validates():
    # Minimal valid payload
    payload = UserCreate(name="Asha", mobile_number="+919876543210", language_pref="hi")
    assert payload.name == "Asha"
    assert payload.language_pref == "hi"

def test_user_create_defaults_language():
    payload = UserCreate(name="Ravi", mobile_number="+911234567890")
    assert payload.language_pref == "en"

def test_user_out_from_orm_like():
    # Simulate ORM row
    now = datetime.utcnow()
    row = type("Row", (), dict(
        id="abc-123",
        name="Asha",
        mobile_number="+919876543210",
        language_pref="hi",
        created_at=now - timedelta(seconds=5),
        updated_at=now,
    ))()
    out = UserOut.model_validate(row)  # from_attributes=True lets this work
    assert out.id == "abc-123"
    assert out.mobile_number.endswith("3210")

def test_user_create_invalid_number():
    with pytest.raises(Exception):
        UserCreate(name="X", mobile_number="12")  # too short -> validation error
