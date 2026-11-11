"""Focused tests for authenticated PDF upload extraction."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.api.deps import get_order_field_extractor
from app.integrations.deepseek import ExtractionProviderError
from app.integrations.extraction import ExtractedOrderFields
from app.integrations.pdf_processor import ProcessedPdf
from tests.conftest import TEST_DATABASE_URL, auth_header, register_and_login
from tests.pdf_fixtures import (
    SAMPLE_ORDER_LINES,
    VALID_EXTRACTED,
    build_multipage_pdf,
    build_scanned_pdf,
    build_text_pdf,
)


class FakeExtractor:
    def __init__(self, result: ExtractedOrderFields | Exception) -> None:
        self._result = result
        self.calls = 0

    def extract(self, document: ProcessedPdf) -> ExtractedOrderFields:
        self.calls += 1
        assert document.page_count >= 1
        assert len(document.pages) == document.page_count
        if isinstance(self._result, Exception):
            raise self._result
        return self._result


@pytest.fixture()
def upload_client(
    client: TestClient,
) -> Generator[tuple[TestClient, FakeExtractor], None, None]:
    fake = FakeExtractor(VALID_EXTRACTED)
    client.app.dependency_overrides[get_order_field_extractor] = lambda: fake
    yield client, fake
    client.app.dependency_overrides.pop(get_order_field_extractor, None)


def _count_orders() -> int:
    with Session(create_engine(TEST_DATABASE_URL)) as session:
        return int(session.scalar(text("SELECT COUNT(*) FROM orders")) or 0)


def test_successful_extraction_persists_order(
    upload_client: tuple[TestClient, FakeExtractor],
) -> None:
    client, fake = upload_client
    token = register_and_login(client, "upload.success@example.com")
    pdf_bytes = build_text_pdf(SAMPLE_ORDER_LINES)

    response = client.post(
        "/api/orders/upload",
        headers=auth_header(token),
        files={"file": ("order.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "created"
    assert body["saved"] is True
    assert body["order_id"] is not None
    assert body["extracted"]["patient_first_name"] == "Jane"
    assert body["errors"] == {}
    assert fake.calls == 1
    assert _count_orders() == 1


def test_scanned_document_extraction(
    upload_client: tuple[TestClient, FakeExtractor],
) -> None:
    client, _fake = upload_client
    token = register_and_login(client, "upload.scanned@example.com")
    pdf_bytes = build_scanned_pdf(SAMPLE_ORDER_LINES)

    response = client.post(
        "/api/orders/upload",
        headers=auth_header(token),
        files={"file": ("scan.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "created"
    assert response.json()["saved"] is True


def test_multipage_document_extraction(
    upload_client: tuple[TestClient, FakeExtractor],
) -> None:
    client, fake = upload_client
    token = register_and_login(client, "upload.multipage@example.com")
    pdf_bytes = build_multipage_pdf()

    response = client.post(
        "/api/orders/upload",
        headers=auth_header(token),
        files={"file": ("multi.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    assert response.json()["saved"] is True
    assert fake.calls == 1


def test_missing_fields_needs_review_without_persistence(
    client: TestClient,
) -> None:
    fake = FakeExtractor(
        ExtractedOrderFields(
            patient_first_name="Jane",
            patient_last_name=None,
            patient_dob="1988-04-12",
            provider_name="Dr. Example",
            provider_npi="1234567893",
        )
    )
    client.app.dependency_overrides[get_order_field_extractor] = lambda: fake
    token = register_and_login(client, "upload.missing@example.com")

    response = client.post(
        "/api/orders/upload",
        headers=auth_header(token),
        files={"file": ("order.pdf", build_text_pdf(SAMPLE_ORDER_LINES), "application/pdf")},
    )
    client.app.dependency_overrides.pop(get_order_field_extractor, None)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "needs_review"
    assert body["saved"] is False
    assert body["order_id"] is None
    assert "patient_last_name" in body["errors"]
    assert _count_orders() == 0


def test_invalid_npi_needs_review_without_persistence(client: TestClient) -> None:
    fake = FakeExtractor(
        ExtractedOrderFields(
            patient_first_name="Jane",
            patient_last_name="Doe",
            patient_dob="1988-04-12",
            provider_name="Dr. Example",
            provider_npi="1234567890",
        )
    )
    client.app.dependency_overrides[get_order_field_extractor] = lambda: fake
    token = register_and_login(client, "upload.badnpi@example.com")

    response = client.post(
        "/api/orders/upload",
        headers=auth_header(token),
        files={"file": ("order.pdf", build_text_pdf(SAMPLE_ORDER_LINES), "application/pdf")},
    )
    client.app.dependency_overrides.pop(get_order_field_extractor, None)

    assert response.status_code == 200
    body = response.json()
    assert body["saved"] is False
    assert "provider_npi" in body["errors"]
    assert _count_orders() == 0


def test_invalid_dob_needs_review_without_persistence(client: TestClient) -> None:
    fake = FakeExtractor(
        ExtractedOrderFields(
            patient_first_name="Jane",
            patient_last_name="Doe",
            patient_dob="2999-01-01",
            provider_name="Dr. Example",
            provider_npi="1234567893",
        )
    )
    client.app.dependency_overrides[get_order_field_extractor] = lambda: fake
    token = register_and_login(client, "upload.baddob@example.com")

    response = client.post(
        "/api/orders/upload",
        headers=auth_header(token),
        files={"file": ("order.pdf", build_text_pdf(SAMPLE_ORDER_LINES), "application/pdf")},
    )
    client.app.dependency_overrides.pop(get_order_field_extractor, None)

    assert response.status_code == 200
    assert response.json()["saved"] is False
    assert "patient_dob" in response.json()["errors"]
    assert _count_orders() == 0


def test_malformed_model_output_returns_bad_gateway(client: TestClient) -> None:
    fake = FakeExtractor(ExtractionProviderError("malformed"))
    client.app.dependency_overrides[get_order_field_extractor] = lambda: fake
    token = register_and_login(client, "upload.malformed@example.com")

    response = client.post(
        "/api/orders/upload",
        headers=auth_header(token),
        files={"file": ("order.pdf", build_text_pdf(SAMPLE_ORDER_LINES), "application/pdf")},
    )
    client.app.dependency_overrides.pop(get_order_field_extractor, None)

    assert response.status_code == 502
    assert _count_orders() == 0


def test_unauthorized_upload_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/orders/upload",
        files={"file": ("order.pdf", build_text_pdf(SAMPLE_ORDER_LINES), "application/pdf")},
    )
    assert response.status_code == 401


def test_non_pdf_upload_rejected(
    upload_client: tuple[TestClient, FakeExtractor],
) -> None:
    client, fake = upload_client
    token = register_and_login(client, "upload.nonpdf@example.com")
    response = client.post(
        "/api/orders/upload",
        headers=auth_header(token),
        files={"file": ("notes.txt", b"not a pdf", "text/plain")},
    )
    assert response.status_code == 400
    assert fake.calls == 0
    assert _count_orders() == 0


def test_oversized_pdf_rejected_without_extraction(
    upload_client: tuple[TestClient, FakeExtractor],
) -> None:
    client, fake = upload_client
    token = register_and_login(client, "upload.oversize@example.com")
    oversized = b"%PDF-1.4\n" + (b"0" * (11 * 1024 * 1024))
    response = client.post(
        "/api/orders/upload",
        headers=auth_header(token),
        files={"file": ("big.pdf", oversized, "application/pdf")},
    )
    assert response.status_code == 400
    assert fake.calls == 0
    assert _count_orders() == 0


def test_upstream_api_failure_returns_bad_gateway(client: TestClient) -> None:
    fake = FakeExtractor(ExtractionProviderError("upstream down"))
    client.app.dependency_overrides[get_order_field_extractor] = lambda: fake
    token = register_and_login(client, "upload.upstream@example.com")

    response = client.post(
        "/api/orders/upload",
        headers=auth_header(token),
        files={"file": ("order.pdf", build_text_pdf(SAMPLE_ORDER_LINES), "application/pdf")},
    )
    client.app.dependency_overrides.pop(get_order_field_extractor, None)

    assert response.status_code == 502
    assert response.json()["detail"] == "Document extraction failed"
    assert _count_orders() == 0
