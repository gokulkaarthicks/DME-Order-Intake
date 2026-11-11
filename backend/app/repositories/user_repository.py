"""Database operations for User records."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import User


class UserRepository:
    """Repository responsible exclusively for user persistence queries."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, user_id: UUID) -> User | None:
        """Return a user by primary key, or None when not found."""
        return self._session.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        """Return a user by normalized email, or None when not found."""
        statement = select(User).where(User.email == email)
        return self._session.scalar(statement)

    def create(self, *, email: str, password_hash: str) -> User:
        """Insert a new user and flush so database defaults and constraints apply."""
        user = User(email=email, password_hash=password_hash)
        self._session.add(user)
        self._session.flush()
        return user
