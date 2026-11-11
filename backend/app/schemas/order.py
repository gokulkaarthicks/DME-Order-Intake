"""Pydantic schemas for order create, update, and public responses."""

from __future__ import annotations

from datetime import date, datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

from app.core.npi import is_valid_npi

NonEmptyName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=255),
]


class OrderCreate(BaseModel):
    """Payload for creating a durable medical equipment order."""

    model_config = ConfigDict(extra="forbid")

    patient_first_name: NonEmptyName
    patient_last_name: NonEmptyName
    patient_dob: date
    provider_name: NonEmptyName
    provider_npi: str = Field(min_length=10, max_length=10)

    @field_validator("patient_dob")
    @classmethod
    def reject_future_dob(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("patient_dob cannot be in the future")
        return value

    @field_validator("provider_npi")
    @classmethod
    def validate_npi(cls, value: str) -> str:
        normalized = value.strip()
        if not is_valid_npi(normalized):
            raise ValueError("provider_npi must be a valid 10-digit NPI")
        return normalized


class OrderUpdate(BaseModel):
    """Payload for partially updating an owned order."""

    model_config = ConfigDict(extra="forbid")

    patient_first_name: NonEmptyName | None = None
    patient_last_name: NonEmptyName | None = None
    patient_dob: date | None = None
    provider_name: NonEmptyName | None = None
    provider_npi: str | None = Field(default=None, min_length=10, max_length=10)

    @model_validator(mode="after")
    def reject_explicit_nulls(self) -> OrderUpdate:
        for field_name in self.model_fields_set:
            if getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null")
        return self

    @field_validator("patient_dob")
    @classmethod
    def reject_future_dob(cls, value: date | None) -> date | None:
        if value is not None and value > date.today():
            raise ValueError("patient_dob cannot be in the future")
        return value

    @field_validator("provider_npi")
    @classmethod
    def validate_npi(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        if not is_valid_npi(normalized):
            raise ValueError("provider_npi must be a valid 10-digit NPI")
        return normalized


class OrderPublic(BaseModel):
    """Public order representation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    patient_first_name: str
    patient_last_name: str
    patient_dob: date
    provider_name: str
    provider_npi: str
    created_at: datetime
    updated_at: datetime
