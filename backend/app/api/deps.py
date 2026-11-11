"""FastAPI dependency injection conventions for shared resources."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService

SettingsDep = Annotated[Settings, Depends(get_settings)]
DbSessionDep = Annotated[Session, Depends(get_db)]


def get_user_repository(session: DbSessionDep) -> UserRepository:
    """Build a request-scoped user repository."""
    return UserRepository(session)


UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]


def get_auth_service(
    session: DbSessionDep,
    settings: SettingsDep,
    user_repository: UserRepositoryDep,
) -> AuthService:
    """Build a request-scoped authentication service."""
    return AuthService(
        session=session,
        user_repository=user_repository,
        settings=settings,
    )


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
