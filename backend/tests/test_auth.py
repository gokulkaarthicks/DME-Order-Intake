"""Focused authentication checks that must remain operational."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_register_login_and_health(client: TestClient) -> None:
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    register = client.post(
        "/api/auth/register",
        json={"username": " Auth_User ", "password": "SecurePass123"},
    )
    assert register.status_code == 201
    body = register.json()
    assert body["username"] == "auth_user"
    assert "password_hash" not in body

    duplicate = client.post(
        "/api/auth/register",
        json={"username": "auth_user", "password": "SecurePass123"},
    )
    assert duplicate.status_code == 409

    duplicate_case = client.post("/api/auth/register", json={"username": "AUTH_USER", "password": "SecurePass123"})
    assert duplicate_case.status_code == 409

    login = client.post(
        "/api/auth/login",
        json={"username": "auth_user", "password": "SecurePass123"},
    )
    assert login.status_code == 200
    assert login.json()["token_type"] == "bearer"
    assert login.json()["access_token"]

    bad_login = client.post(
        "/api/auth/login",
        json={"username": "auth_user", "password": "wrong-password"},
    )
    assert bad_login.status_code == 401


def test_invalid_usernames(client: TestClient) -> None:
    for username in ("", "  ", "ab", "a" * 33, "name.with.dot", "name@example.com", "non-ascii_é"):
        for route in ("register", "login"):
            response = client.post(f"/api/auth/{route}", json={"username": username, "password": "SecurePass123"})
            assert response.status_code == 422, (username, route, response.text)
