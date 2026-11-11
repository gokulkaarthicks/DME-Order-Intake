"""Persistent review tests against the migrated PostgreSQL test database."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from app.api.deps import get_order_field_extractor
from app.integrations.extraction import ExtractedOrderFields
from tests.conftest import TEST_DATABASE_URL, auth_header, register_and_login
from tests.pdf_fixtures import build_text_pdf, SAMPLE_ORDER_LINES


class MissingExtractor:
    calls = 0
    def extract(self, document):
        self.calls += 1
        return ExtractedOrderFields("Jane", None, "1988-04-12", "Dr Example", "1234567893")


def test_persistent_review_and_atomic_resolution(client: TestClient, valid_order_payload: dict[str, str]) -> None:
    fake = MissingExtractor()
    client.app.dependency_overrides[get_order_field_extractor] = lambda: fake
    owner = auth_header(register_and_login(client, "review_owner"))
    other = auth_header(register_and_login(client, "review_other"))
    upload = client.post("/api/orders/upload", headers=owner,
        files={"file": ("order.pdf", build_text_pdf(SAMPLE_ORDER_LINES), "application/pdf")}).json()
    assert upload["status"] == "needs_review" and not upload["saved"]
    payload = {"extracted": upload["extracted"], "review_token": upload["review_token"]}
    assert client.post("/api/reviews", headers=other, json=payload).status_code == 400
    tampered = {**payload, "extracted": {**payload["extracted"], "patient_last_name": "Changed"}}
    assert client.post("/api/reviews", headers=owner, json=tampered).status_code == 400
    saved = client.post("/api/reviews", headers=owner, json=payload)
    assert saved.status_code == 201
    review = saved.json()
    assert review["extracted"]["patient_last_name"] is None
    assert "patient_last_name" in review["errors"]
    assert client.post("/api/reviews", headers=owner, json=payload).json()["id"] == review["id"]
    assert client.get("/api/reviews", headers=other).json() == []
    assert client.post(f"/api/reviews/{review['id']}/resolve", headers=other, json=valid_order_payload).status_code == 404
    login = client.post("/api/auth/login", json={"username": "review_owner", "password": "SecurePass123"})
    new_headers = auth_header(login.json()["access_token"])
    assert client.get("/api/reviews", headers=new_headers).json()[0]["errors"] == review["errors"]
    invalid = {**valid_order_payload, "provider_npi": "1234567890"}
    assert client.post(f"/api/reviews/{review['id']}/resolve", headers=new_headers, json=invalid).status_code == 422
    barrier = Barrier(2)
    def resolve():
        barrier.wait(timeout=10)
        return client.post(f"/api/reviews/{review['id']}/resolve", headers=new_headers, json=valid_order_payload).status_code
    with ThreadPoolExecutor(max_workers=2) as executor:
        statuses = list(executor.map(lambda _: resolve(), range(2)))
    assert sorted(statuses) == [200, 409]
    assert client.get("/api/reviews", headers=new_headers).json() == []
    assert client.post("/api/reviews", headers=new_headers, json=payload).status_code == 409
    assert len(client.get("/api/orders", headers=new_headers).json()) == 1
    assert fake.calls == 1
    engine = create_engine(TEST_DATABASE_URL)
    with engine.connect() as conn:
        assert conn.execute(text("SELECT status FROM pending_reviews WHERE id = :id"), {"id": review["id"]}).scalar_one() == "resolved"
        assert conn.execute(text("SELECT count(*) FROM orders")).scalar_one() == 1
    engine.dispose()


def test_resolution_rolls_back_order_if_transaction_fails(client: TestClient, valid_order_payload: dict[str, str], monkeypatch) -> None:
    from app.repositories.order_repository import OrderRepository
    fake = MissingExtractor()
    client.app.dependency_overrides[get_order_field_extractor] = lambda: fake
    headers = auth_header(register_and_login(client, "review_rollback"))
    upload = client.post("/api/orders/upload", headers=headers,
        files={"file": ("order.pdf", build_text_pdf(SAMPLE_ORDER_LINES), "application/pdf")}).json()
    review = client.post("/api/reviews", headers=headers,
        json={"extracted": upload["extracted"], "review_token": upload["review_token"]}).json()
    original = OrderRepository.create
    def fail_after_flush(self, **kwargs):
        original(self, **kwargs)
        raise RuntimeError("simulated transaction failure")
    monkeypatch.setattr(OrderRepository, "create", fail_after_flush)
    try:
        client.post(f"/api/reviews/{review['id']}/resolve", headers=headers, json=valid_order_payload)
    except RuntimeError:
        pass
    else:
        raise AssertionError("Expected the simulated failure")
    assert len(client.get("/api/reviews", headers=headers).json()) == 1
    assert client.get("/api/orders", headers=headers).json() == []


def test_concurrent_save_and_immediate_correction_use_one_proof(client: TestClient, valid_order_payload: dict[str, str]) -> None:
    import json
    fake = MissingExtractor()
    client.app.dependency_overrides[get_order_field_extractor] = lambda: fake
    headers = auth_header(register_and_login(client, "review_race"))
    files = {"file": ("order.pdf", build_text_pdf(SAMPLE_ORDER_LINES), "application/pdf")}
    upload = client.post("/api/orders/upload", headers=headers, files=files).json()
    payload = {"extracted": upload["extracted"], "review_token": upload["review_token"]}
    barrier = Barrier(2)
    def save():
        barrier.wait(timeout=10)
        return client.post("/api/reviews", headers=headers, json=payload).status_code
    def correct():
        barrier.wait(timeout=10)
        return client.post("/api/orders/upload", headers=headers, files=files,
            data={"corrections": json.dumps(valid_order_payload), "review_token": upload["review_token"]}).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        first, second = pool.submit(save), pool.submit(correct)
        statuses = (first.result(), second.result())
    assert statuses in {(201, 400), (409, 200)}
    reviews = client.get("/api/reviews", headers=headers).json()
    orders = client.get("/api/orders", headers=headers).json()
    assert len(reviews) + len(orders) == 1
