"""FastAPI dependency injection conventions for shared resources."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security import TokenValidationError, verify_access_token
from app.db.models import User
from app.db.session import get_db
from app.integrations.deepseek import DeepSeekExtractor
from app.integrations.extraction import OrderFieldExtractor
from app.integrations.pdf_processor import PDFProcessor
from app.repositories.order_repository import OrderRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.extraction_service import ExtractionService
from app.services.order_service import OrderService

SettingsDep = Annotated[Settings, Depends(get_settings)]
DbSessionDep = Annotated[Session, Depends(get_db)]

_bearer_scheme = HTTPBearer(auto_error=False)


def get_user_repository(session: DbSessionDep) -> UserRepository:
    """Build a request-scoped user repository."""
    return UserRepository(session)


UserRepositoryDep = Annotated[UserRepository, Depends(get_user_repository)]


def get_order_repository(session: DbSessionDep) -> OrderRepository:
    """Build a request-scoped order repository."""
    return OrderRepository(session)


OrderRepositoryDep = Annotated[OrderRepository, Depends(get_order_repository)]


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


def get_order_service(
    session: DbSessionDep,
    order_repository: OrderRepositoryDep,
) -> OrderService:
    """Build a request-scoped order service."""
    return OrderService(
        session=session,
        order_repository=order_repository,
    )


OrderServiceDep = Annotated[OrderService, Depends(get_order_service)]


def get_pdf_processor(settings: SettingsDep) -> PDFProcessor:
    """Build the PDF processor from application settings."""
    return PDFProcessor(
        max_pages=settings.pdf_max_pages,
        render_dpi=settings.pdf_render_dpi,
    )


PdfProcessorDep = Annotated[PDFProcessor, Depends(get_pdf_processor)]


def get_order_field_extractor(settings: SettingsDep) -> OrderFieldExtractor:
    """Build the configured extraction provider adapter."""
    return DeepSeekExtractor(settings)


OrderFieldExtractorDep = Annotated[OrderFieldExtractor, Depends(get_order_field_extractor)]


def get_extraction_service(
    settings: SettingsDep,
    pdf_processor: PdfProcessorDep,
    extractor: OrderFieldExtractorDep,
    order_service: OrderServiceDep,
) -> ExtractionService:
    """Build a request-scoped extraction orchestration service."""
    return ExtractionService(
        pdf_processor=pdf_processor,
        extractor=extractor,
        order_service=order_service,
        max_upload_bytes=settings.pdf_max_upload_bytes,
    )


ExtractionServiceDep = Annotated[ExtractionService, Depends(get_extraction_service)]


def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(_bearer_scheme),
    ],
    settings: SettingsDep,
    user_repository: UserRepositoryDep,
) -> User:
    """Resolve the authenticated user exclusively from a verified Bearer JWT."""
    if (
        credentials is None
        or credentials.scheme.lower() != "bearer"
        or not credentials.credentials
    ):
        raise _unauthorized()

    try:
        user_id = verify_access_token(credentials.credentials, settings)
    except TokenValidationError as exc:
        raise _unauthorized() from exc

    user = user_repository.get_by_id(user_id)
    if user is None:
        raise _unauthorized()

    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


def _unauthorized() -> HTTPException:
    """Build a consistent 401 response for authentication failures."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
