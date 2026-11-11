"""Response schemas for PDF upload extraction outcomes."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.order import OrderPublic


class ExtractedFieldsResponse(BaseModel):
    """Nullable extracted business fields returned to the client."""

    patient_first_name: str | None = None
    patient_last_name: str | None = None
    patient_dob: str | None = None
    provider_name: str | None = None
    provider_npi: str | None = None


class OrderUploadResponse(BaseModel):
    """Typed upload result distinguishing created orders from review-needed cases."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["created", "needs_review"]
    saved: bool
    order_id: UUID | None = None
    order: OrderPublic | None = None
    extracted: ExtractedFieldsResponse
    errors: dict[str, str] = Field(default_factory=dict)
    review_token: str | None = None
