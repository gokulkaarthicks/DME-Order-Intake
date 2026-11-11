"""Authentication business logic for registration and login."""

from __future__ import annotations

import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserLoginRequest, UserRegisterRequest

logger = logging.getLogger(__name__)


class AuthError(Exception):
    """Base class for authentication domain errors."""


class DuplicateUsernameError(AuthError):
    """Raised when registration targets a username that already exists."""


class InvalidCredentialsError(AuthError):
    """Raised when login credentials are invalid."""


class AuthService:
    """Coordinates registration and login without owning HTTP concerns."""

    def __init__(
        self,
        *,
        session: Session,
        user_repository: UserRepository,
        settings: Settings,
    ) -> None:
        self._session = session
        self._users = user_repository
        self._settings = settings

    def register(self, payload: UserRegisterRequest) -> User:
        """Create a DME employee account for a unique username."""
        if self._users.get_by_username(payload.username) is not None:
            raise DuplicateUsernameError("Username already registered")

        password_hash = hash_password(payload.password)
        try:
            user = self._users.create(
                username=payload.username,
                password_hash=password_hash,
            )
            self._session.commit()
        except IntegrityError as exc:
            self._session.rollback()
            if _is_unique_username_violation(exc):
                raise DuplicateUsernameError("Username already registered") from exc
            logger.exception("Unexpected integrity error during registration")
            raise
        except Exception:
            self._session.rollback()
            raise

        self._session.refresh(user)
        return user

    def login(self, payload: UserLoginRequest) -> str:
        """Authenticate a user and return a signed JWT access token."""
        user = self._users.get_by_username(payload.username)
        if user is None or not verify_password(payload.password, user.password_hash):
            raise InvalidCredentialsError("Invalid username or password")

        return create_access_token(subject=user.id, settings=self._settings)


def _is_unique_username_violation(exc: IntegrityError) -> bool:
    """Detect unique-username constraint violations without exposing SQL details."""
    orig = getattr(exc, "orig", None)
    sqlstate = getattr(orig, "sqlstate", None)
    if sqlstate == "23505":
        return True

    message = str(orig).lower() if orig is not None else str(exc).lower()
    return "ix_users_username_lower" in message or (
        "users" in message and "username" in message and "unique" in message
    )
