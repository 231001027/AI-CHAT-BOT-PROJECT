"""
Password hashing and JWT issuing for staff accounts.

Only departmental staff authenticate. Patients are registered per visit without
an account, so nothing here is on the patient path.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import bcrypt
from jose import JWTError, jwt

from app.config import get_settings

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"

# bcrypt hashes at most 72 bytes and rejects anything longer outright. Truncating
# is the standard handling; the alternative is rejecting long passphrases.
BCRYPT_MAX_BYTES = 72

BCRYPT_ROUNDS = 12


def _prepare(password: str) -> bytes:
    encoded = password.encode("utf-8")
    if len(encoded) <= BCRYPT_MAX_BYTES:
        return encoded
    # Trim to the byte limit without splitting a multi-byte character.
    return encoded[:BCRYPT_MAX_BYTES].decode("utf-8", errors="ignore").encode("utf-8")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_prepare(password), bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Never raises — a malformed or empty stored hash is treated as a failed login."""
    if not plain or not hashed:
        return False
    try:
        return bcrypt.checkpw(_prepare(plain), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def _encode(subject: str, token_type: str, minutes: int, extra: Optional[dict[str, Any]]) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + timedelta(minutes=minutes),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_access_token(subject: str, extra: Optional[dict[str, Any]] = None) -> str:
    return _encode(subject, ACCESS_TOKEN_TYPE, get_settings().jwt_expire_minutes, extra)


def create_refresh_token(subject: str, extra: Optional[dict[str, Any]] = None) -> str:
    return _encode(
        subject, REFRESH_TOKEN_TYPE, get_settings().jwt_refresh_expire_minutes, extra
    )


def decode_token(token: str, *, expected_type: Optional[str] = None) -> Optional[dict[str, Any]]:
    """
    Decode and verify a token.

    Returns None on any failure. ``expected_type`` prevents a refresh token from
    being presented as an access token, which would silently extend its reach.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None

    if expected_type is not None and payload.get("type") != expected_type:
        return None
    return payload


def decode_access_token(token: str) -> Optional[dict[str, Any]]:
    return decode_token(token, expected_type=ACCESS_TOKEN_TYPE)


def decode_refresh_token(token: str) -> Optional[dict[str, Any]]:
    return decode_token(token, expected_type=REFRESH_TOKEN_TYPE)
