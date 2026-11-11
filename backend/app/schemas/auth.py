"""Pydantic schemas for authentication requests and public user responses."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator

NormalizedEmail = Annotated[
    EmailStr,
    StringConstraints(strip_whitespace=True, to_lower=True, max_length=320),
]


class UserRegisterRequest(BaseModel):
    """Payload for DME employee registration."""

    email: NormalizedEmail
    password: str = Field(min_length=8, max_length=128)


class UserLoginRequest(BaseModel):
    """Payload for DME employee login."""

    email: NormalizedEmail
    password: str = Field(min_length=1, max_length=128)


class AccessTokenResponse(BaseModel):
    """Bearer access token returned after successful authentication."""

    access_token: str
    token_type: str = "bearer"


class UserPublic(BaseModel):
    """Public user representation that never includes password material."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    created_at: datetime

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower()
        return value
