"""Optional live DeepSeek verification for PDF extraction."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from tests.conftest import auth_header, register_and_login
from tests.pdf_fixtures import SAMPLE_ORDER_LINES, build_scanned_pdf

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "").strip()


@pytest.mark.skipif(
    not DEEPSEEK_API_KEY,
    reason="DEEPSEEK_API_KEY is not configured; live model verification remains pending",
)
def test_live_deepseek_scanned_pdf_extraction(client: TestClient) -> None:
    token = register_and_login(client, "upload.live@example.com")
    pdf_bytes = build_scanned_pdf(SAMPLE_ORDER_LINES)

    response = client.post(
        "/api/orders/upload",
        headers=auth_header(token),
        files={"file": ("live-scan.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] in {"created", "needs_review"}
    assert "extracted" in body
    assert set(body["extracted"]) == {
        "patient_first_name",
        "patient_last_name",
        "patient_dob",
        "provider_name",
        "provider_npi",
    }
