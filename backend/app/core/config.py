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

    database_url: str = Field(
        default="postgresql+psycopg://dme:dme@127.0.0.1:5434/dme_order_intake",
        description="SQLAlchemy database URL (PostgreSQL + Psycopg 3)",
    )
    db_pool_size: int = Field(default=5, description="SQLAlchemy connection pool size")
    db_max_overflow: int = Field(
        default=10,
        description="Additional connections allowed above the pool size",
    )

    jwt_secret_key: str = Field(
        default="",
        description="Secret used to sign JWT access tokens (required for auth; min 32 chars)",
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm",
    )
    access_token_expire_minutes: int = Field(
        default=60,
        ge=1,
        description="Access token lifetime in minutes",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance for dependency injection."""
    return Settings()
