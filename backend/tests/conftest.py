"""Shared pytest fixtures using an isolated PostgreSQL test database."""

from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

TEST_DATABASE_URL = (
    "postgresql+psycopg://dme:dme@127.0.0.1:5434/dme_order_intake_test"
)
TEST_JWT_SECRET = "test-only-jwt-secret-key-32chars-min"


def _ensure_test_database() -> None:
    admin_engine = create_engine(
        "postgresql+psycopg://dme:dme@127.0.0.1:5434/postgres",
        isolation_level="AUTOCOMMIT",
    )
    with admin_engine.connect() as connection:
        exists = connection.execute(
            text("SELECT 1 FROM pg_database WHERE datname = 'dme_order_intake_test'")
        ).scalar()
        if not exists:
            connection.execute(text("CREATE DATABASE dme_order_intake_test"))
    admin_engine.dispose()


def _run_migrations(database_url: str) -> None:
    os.environ["DATABASE_URL"] = database_url
    from app.core.config import get_settings

    get_settings.cache_clear()
    config = Config("alembic.ini")
    command.upgrade(config, "head")


@pytest.fixture(scope="session")
def test_engine() -> Generator[Engine, None, None]:
    _ensure_test_database()
    _run_migrations(TEST_DATABASE_URL)
    engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    yield engine
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_tables(test_engine: Engine) -> Generator[None, None, None]:
    yield
    with test_engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE orders, users RESTART IDENTITY CASCADE"))


@pytest.fixture()
def client(test_engine: Engine, monkeypatch: pytest.MonkeyPatch) -> Generator[TestClient, None, None]:
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    monkeypatch.setenv("JWT_SECRET_KEY", TEST_JWT_SECRET)
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")

    from app.core.config import get_settings
    from app.db.session import dispose_engine
    from app.main import create_app

    get_settings.cache_clear()
    dispose_engine()

    application = create_app()
    with TestClient(application) as test_client:
        yield test_client

    dispose_engine()
    get_settings.cache_clear()


@pytest.fixture()
def valid_order_payload() -> dict[str, str]:
    return {
        "patient_first_name": "Ada",
        "patient_last_name": "Lovelace",
        "patient_dob": "1815-12-10",
        "provider_name": "Dr. Example",
        "provider_npi": "1234567893",
    }


def register_and_login(client: TestClient, email: str, password: str = "SecurePass123") -> str:
    register = client.post(
        "/api/auth/register",
        json={"email": email, "password": password},
    )
    assert register.status_code == 201, register.text
    login = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200, login.text
    return login.json()["access_token"]


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
