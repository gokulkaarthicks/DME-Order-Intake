"""Centralized environment-based application settings."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables and optional .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="DME Order Intake", description="Public application name")
    environment: str = Field(default="development", description="Runtime environment name")
    debug: bool = Field(default=False, description="Enable verbose error detail in responses")
    log_level: str = Field(default="INFO", description="Root logger level")
    api_prefix: str = Field(default="/api", description="Prefix for versioned API routes")
    host: str = Field(default="0.0.0.0", description="Uvicorn bind host")
    port: int = Field(default=8000, description="Uvicorn bind port")


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance for dependency injection."""
    return Settings()
