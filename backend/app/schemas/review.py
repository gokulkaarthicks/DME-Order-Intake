"""Human review request and response contracts."""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from app.schemas.extraction import ExtractedFieldsResponse


class ReviewSaveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    review_token: str
    extracted: ExtractedFieldsResponse


class ReviewPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    extracted: ExtractedFieldsResponse
    errors: dict[str, str]
    status: str
    created_at: datetime
    updated_at: datetime
