"""Focused automated tests for authenticated order CRUD and isolation."""

from __future__ import annotations

from datetime import date, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from app.db.models import Order
from tests.conftest import TEST_DATABASE_URL, auth_header, register_and_login


def test_create_list_get_update_delete_order(
    client: TestClient,
    valid_order_payload: dict[str, str],
) -> None:
    token = register_and_login(client, "owner")
    headers = auth_header(token)

    create_response = client.post("/api/orders", json=valid_order_payload, headers=headers)
    assert create_response.status_code == 201
    created = create_response.json()
    order_id = created["id"]
    assert created["patient_first_name"] == "Ada"
    assert created["provider_npi"] == "1234567893"
    assert "password_hash" not in created

    with Session(create_engine(TEST_DATABASE_URL)) as session:
        persisted = session.scalar(select(Order).where(Order.id == order_id))
        assert persisted is not None
        assert persisted.patient_last_name == "Lovelace"

    list_response = client.get("/api/orders", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    get_response = client.get(f"/api/orders/{order_id}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["id"] == order_id

    update_response = client.patch(
        f"/api/orders/{order_id}",
        json={"provider_name": "Dr. Updated"},
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["provider_name"] == "Dr. Updated"
    assert update_response.json()["patient_first_name"] == "Ada"

    with Session(create_engine(TEST_DATABASE_URL)) as session:
        persisted = session.scalar(select(Order).where(Order.id == order_id))
        assert persisted is not None
        assert persisted.provider_name == "Dr. Updated"

    delete_response = client.delete(f"/api/orders/{order_id}", headers=headers)
    assert delete_response.status_code == 204

    missing = client.get(f"/api/orders/{order_id}", headers=headers)
    assert missing.status_code == 404


def test_invalid_dob_and_npi_rejected(
    client: TestClient,
    valid_order_payload: dict[str, str],
) -> None:
    token = register_and_login(client, "validator")
    headers = auth_header(token)

    future_dob = dict(valid_order_payload)
    future_dob["patient_dob"] = (date.today() + timedelta(days=1)).isoformat()
    assert client.post("/api/orders", json=future_dob, headers=headers).status_code == 422

    bad_npi = dict(valid_order_payload)
    bad_npi["provider_npi"] = "1234567890"
    assert client.post("/api/orders", json=bad_npi, headers=headers).status_code == 422

    with Session(create_engine(TEST_DATABASE_URL)) as session:
        count = session.scalar(text("SELECT COUNT(*) FROM orders"))
        assert count == 0


def test_missing_and_blank_required_fields(
    client: TestClient,
    valid_order_payload: dict[str, str],
) -> None:
    token = register_and_login(client, "required")
    headers = auth_header(token)

    missing = dict(valid_order_payload)
    missing.pop("patient_first_name")
    assert client.post("/api/orders", json=missing, headers=headers).status_code == 422

    blank = dict(valid_order_payload)
    blank["patient_last_name"] = "   "
    assert client.post("/api/orders", json=blank, headers=headers).status_code == 422


def test_partial_update_rejects_null_and_blank(
    client: TestClient,
    valid_order_payload: dict[str, str],
) -> None:
    token = register_and_login(client, "patchuser")
    headers = auth_header(token)
    created = client.post("/api/orders", json=valid_order_payload, headers=headers)
    order_id = created.json()["id"]

    null_update = client.patch(
        f"/api/orders/{order_id}",
        json={"provider_name": None},
        headers=headers,
    )
    assert null_update.status_code == 422

    blank_update = client.patch(
        f"/api/orders/{order_id}",
        json={"provider_name": "  "},
        headers=headers,
    )
    assert blank_update.status_code == 422

    unchanged = client.get(f"/api/orders/{order_id}", headers=headers)
    assert unchanged.json()["provider_name"] == "Dr. Example"


def test_unauthenticated_order_access_returns_401(
    client: TestClient,
    valid_order_payload: dict[str, str],
) -> None:
    assert client.post("/api/orders", json=valid_order_payload).status_code == 401
    assert client.get("/api/orders").status_code == 401
    assert client.get(f"/api/orders/{uuid4()}").status_code == 401
    assert client.patch(
        f"/api/orders/{uuid4()}",
        json={"provider_name": "Nope"},
    ).status_code == 401
    assert client.delete(f"/api/orders/{uuid4()}").status_code == 401


def test_cross_user_isolation(
    client: TestClient,
    valid_order_payload: dict[str, str],
) -> None:
    token_a = register_and_login(client, "user_a")
    token_b = register_and_login(client, "user_b")
    headers_a = auth_header(token_a)
    headers_b = auth_header(token_b)

    created = client.post("/api/orders", json=valid_order_payload, headers=headers_a)
    assert created.status_code == 201
    order_id = created.json()["id"]

    assert client.get(f"/api/orders/{order_id}", headers=headers_b).status_code == 404
    assert client.patch(
        f"/api/orders/{order_id}",
        json={"provider_name": "Hijack"},
        headers=headers_b,
    ).status_code == 404
    assert client.delete(f"/api/orders/{order_id}", headers=headers_b).status_code == 404

    list_b = client.get("/api/orders", headers=headers_b)
    assert list_b.status_code == 200
    assert list_b.json() == []

    list_a = client.get("/api/orders", headers=headers_a)
    assert list_a.status_code == 200
    assert len(list_a.json()) == 1
    assert list_a.json()[0]["id"] == order_id


def test_validation_errors_do_not_echo_input_payload(
    client: TestClient,
    valid_order_payload: dict[str, str],
) -> None:
    token = register_and_login(client, "novalinput")
    headers = auth_header(token)
    bad = dict(valid_order_payload)
    bad["provider_npi"] = "1234567890"
    response = client.post("/api/orders", json=bad, headers=headers)
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert isinstance(detail, list)
    assert all("input" not in item for item in detail)
    assert all("ctx" not in item for item in detail)


def test_user_specific_listing_order(
    client: TestClient,
    valid_order_payload: dict[str, str],
) -> None:
    token = register_and_login(client, "lister")
    headers = auth_header(token)

    first = dict(valid_order_payload)
    first["patient_first_name"] = "First"
    second = dict(valid_order_payload)
    second["patient_first_name"] = "Second"

    id_first = client.post("/api/orders", json=first, headers=headers).json()["id"]
    id_second = client.post("/api/orders", json=second, headers=headers).json()["id"]

    listed = client.get("/api/orders", headers=headers).json()
    assert [item["id"] for item in listed] == [id_second, id_first]
