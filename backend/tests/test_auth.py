"""Focused authentication checks that must remain operational."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_register_login_and_health(client: TestClient) -> None:
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    register = client.post(
        "/api/auth/register",
        json={"email": "Auth.User@Example.com", "password": "SecurePass123"},
    )
    assert register.status_code == 201
    body = register.json()
    assert body["email"] == "auth.user@example.com"
    assert "password_hash" not in body

    duplicate = client.post(
        "/api/auth/register",
        json={"email": "auth.user@example.com", "password": "SecurePass123"},
    )
    assert duplicate.status_code == 409

    login = client.post(
        "/api/auth/login",
        json={"email": "auth.user@example.com", "password": "SecurePass123"},
    )
    assert login.status_code == 200
    assert login.json()["token_type"] == "bearer"
    assert login.json()["access_token"]

    bad_login = client.post(
        "/api/auth/login",
        json={"email": "auth.user@example.com", "password": "wrong-password"},
    )
    assert bad_login.status_code == 401
