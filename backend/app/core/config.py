"""Centralized environment-based application settings."""

from functools import lru_cache

from pydantic import Field, field_validator
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
        default="",
        description="SQLAlchemy database URL (PostgreSQL + Psycopg 3)",
    )

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        """Use Psycopg 3 for standard PostgreSQL URLs supplied by hosting providers."""
        if isinstance(value, str):
            for prefix in ("postgres://", "postgresql://"):
                if value.startswith(prefix):
                    return "postgresql+psycopg://" + value[len(prefix):]
        return value

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

    deepseek_api_key: str = Field(
        default="",
        description="DeepSeek API key for multimodal PDF extraction",
    )
    deepseek_base_url: str = Field(
        default="https://api.deepseek.com",
        description="DeepSeek API base URL",
    )
    deepseek_model: str = Field(
        default="deepseek-flash",
        description="DeepSeek model identifier",
    )
    deepseek_timeout_seconds: float = Field(
        default=60.0,
        gt=0,
        description="HTTP timeout for DeepSeek extraction requests",
    )
    deepseek_max_retries: int = Field(
        default=2,
        ge=0,
        description="Retries for transient DeepSeek failures",
    )
    pdf_max_upload_bytes: int = Field(
        default=10 * 1024 * 1024,
        gt=0,
        description="Maximum accepted PDF upload size in bytes",
    )
    pdf_max_pages: int = Field(
        default=20,
        ge=1,
        description="Maximum accepted PDF page count",
    )
    pdf_render_dpi: int = Field(
        default=150,
        ge=72,
        description="DPI used when rendering PDF pages to images",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance for dependency injection."""
    return Settings()
