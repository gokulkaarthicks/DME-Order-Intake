"""Authentication HTTP endpoints for registration and login."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.deps import AuthServiceDep
from app.schemas.auth import (
    AccessTokenResponse,
    UserLoginRequest,
    UserPublic,
    UserRegisterRequest,
)
from app.services.auth_service import DuplicateEmailError, InvalidCredentialsError

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    payload: UserRegisterRequest,
    auth_service: AuthServiceDep,
) -> UserPublic:
    """Register a new DME employee account."""
    try:
        user = auth_service.register(payload)
    except DuplicateEmailError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        ) from exc

    return UserPublic.model_validate(user)


@router.post("/login", response_model=AccessTokenResponse)
def login_user(
    payload: UserLoginRequest,
    auth_service: AuthServiceDep,
) -> AccessTokenResponse:
    """Authenticate a DME employee and issue a JWT access token."""
    try:
        access_token = auth_service.login(payload)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return AccessTokenResponse(access_token=access_token)
