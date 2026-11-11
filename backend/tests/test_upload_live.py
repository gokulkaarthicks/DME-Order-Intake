"""Optional live DeepSeek verification for PDF extraction."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from tests.conftest import auth_header, register_and_login
from tests.pdf_fixtures import SAMPLE_ORDER_LINES, build_scanned_pdf


def _deepseek_configured() -> bool:
    get_settings.cache_clear()
    return bool(get_settings().deepseek_api_key.strip())


@pytest.mark.skipif(
    not _deepseek_configured(),
    reason="DEEPSEEK_API_KEY is not configured; live model verification remains pending",
)
def test_live_deepseek_scanned_pdf_extraction(client: TestClient) -> None:
    token = register_and_login(client, "upload_live")
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
    if body["status"] == "created":
        assert body["saved"] is True
        assert body["order_id"] is not None
