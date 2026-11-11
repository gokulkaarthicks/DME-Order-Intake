"""SQLAlchemy engine, session factory, and request-scoped session helpers."""

from __future__ import annotations

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings, get_settings


def create_db_engine(settings: Settings) -> Engine:
    """Create a synchronous SQLAlchemy engine from application settings."""
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
    )


@lru_cache
def get_engine() -> Engine:
    """Return a process-wide cached engine instance."""
    return create_db_engine(get_settings())


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    """Return a cached session factory bound to the application engine."""
    return sessionmaker(
        bind=get_engine(),
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )


def get_db() -> Generator[Session, None, None]:
    """Yield a request-scoped database session and always close it afterward."""
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


def dispose_engine() -> None:
    """Dispose pooled connections and clear cached engine/session factories."""
    if get_engine.cache_info().currsize > 0:
        get_engine().dispose()
    get_engine.cache_clear()
    get_session_factory.cache_clear()
