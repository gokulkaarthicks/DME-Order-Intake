"""Password hashing and JWT helpers, independent of HTTP and persistence."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from pwdlib import PasswordHash

from app.core.config import Settings

_password_hasher = PasswordHash.recommended()


class TokenValidationError(Exception):
    """Raised when a JWT is missing, expired, malformed, or incorrectly signed."""


def hash_password(password: str) -> str:
    """Hash a plaintext password with Argon2."""
    return _password_hasher.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Return True when the plaintext password matches the stored hash."""
    return _password_hasher.verify(plain_password, password_hash)


def create_access_token(*, subject: UUID, settings: Settings) -> str:
    """Create a signed JWT access token with the user UUID as `sub`."""
    _require_jwt_secret(settings)
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(subject),
        "iat": issued_at,
        "exp": expires_at,
    }
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def verify_access_token(token: str, settings: Settings) -> UUID:
    """Validate a JWT and return the authenticated user UUID from `sub`."""
    _require_jwt_secret(settings)
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "sub"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise TokenValidationError("Token has expired") from exc
    except jwt.InvalidTokenError as exc:
        raise TokenValidationError("Invalid token") from exc

    subject = payload.get("sub")
    try:
        return UUID(str(subject))
    except (TypeError, ValueError) as exc:
        raise TokenValidationError("Invalid token subject") from exc


def _require_jwt_secret(settings: Settings) -> None:
    """Reject missing or short signing secrets before any JWT operation."""
    if len(settings.jwt_secret_key) < 32:
        raise TokenValidationError(
            "JWT_SECRET_KEY must be configured with at least 32 characters"
        )
