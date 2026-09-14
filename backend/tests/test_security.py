from app.core.security import create_access_token, decode_access_token, hash_password, verify_password


def test_password_hash_and_verify() -> None:
    hashed = hash_password("secret123")
    assert hashed != "secret123"
    assert verify_password("secret123", hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_jwt_roundtrip() -> None:
    token = create_access_token("42")
    payload = decode_access_token(token)
    assert payload["sub"] == "42"