import pytest
from pydantic import ValidationError

from app.schemas.auth import LoginRequest, UserCreate


def test_login_request_valid() -> None:
    payload = LoginRequest(username="admin", password="admin123")
    assert payload.username == "admin"


def test_user_create_rejects_invalid_role() -> None:
    with pytest.raises(ValidationError):
        UserCreate(username="user1", password="123456", role="superadmin")