"""Database operations for User records."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import User


class UserRepository:
    """Repository responsible exclusively for user persistence queries."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, user_id: UUID) -> User | None:
        """Return a user by primary key, or None when not found."""
        return self._session.get(User, user_id)

    def get_by_username(self, username: str) -> User | None:
        """Return a user by normalized username, or None when not found."""
        statement = select(User).where(func.lower(User.username) == username.strip().lower())
        return self._session.scalar(statement)

    def create(self, *, username: str, password_hash: str) -> User:
        """Insert a new user and flush so database defaults and constraints apply."""
        user = User(username=username, password_hash=password_hash)
        self._session.add(user)
        self._session.flush()
        return user
