"""Pydantic schemas for authentication requests and public user responses."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, StringConstraints


def normalize_username(value: object) -> object:
    if isinstance(value, str):
        return value.strip().lower()
    return value


NormalizedUsername = Annotated[
    str,
    BeforeValidator(normalize_username),
    StringConstraints(min_length=3, max_length=32, pattern=r"^[a-z0-9_]+$"),
]


class UserRegisterRequest(BaseModel):
    """Payload for DME employee registration."""

    username: NormalizedUsername
    password: str = Field(min_length=8, max_length=128)


class UserLoginRequest(BaseModel):
    """Payload for DME employee login."""

    username: NormalizedUsername
    password: str = Field(min_length=1, max_length=128)


class AccessTokenResponse(BaseModel):
    """Bearer access token returned after successful authentication."""

    access_token: str
    token_type: str = "bearer"


class UserPublic(BaseModel):
    """Public user representation that never includes password material."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    created_at: datetime
