"""Schemas for health check responses."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Successful health check payload."""

    status: str = Field(description="Service health status")
    app_name: str = Field(description="Configured application name")
    environment: str = Field(description="Configured runtime environment")
