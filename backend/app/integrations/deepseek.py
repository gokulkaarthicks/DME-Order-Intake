"""DeepSeek multimodal adapter for order-field extraction."""

from __future__ import annotations

import base64
import json
import logging
import re
from typing import Any

import httpx

from app.core.config import Settings
from app.integrations.extraction import ExtractedOrderFields
from app.integrations.pdf_processor import ProcessedPdf

logger = logging.getLogger(__name__)

_FIELD_NAMES = (
    "patient_first_name",
    "patient_last_name",
    "patient_dob",
    "provider_name",
    "provider_npi",
)

_SYSTEM_PROMPT = """
You extract durable medical equipment (DME) order fields from medical documents.
Return ONLY a single JSON object with exactly these keys:
patient_first_name, patient_last_name, patient_dob, provider_name, provider_npi.

Rules:
- Use null for missing, unreadable, conflicting, or genuinely ambiguous values.
- Never invent, guess, or fill speculative values.
- patient_dob must be YYYY-MM-DD when known, otherwise null.
- provider_name and provider_npi must identify the ordering provider, not unrelated clinicians.
- If the same field has conflicting values across pages, return null for that field.
- provider_npi must contain only digits when present.
""".strip()


class ExtractionProviderError(Exception):
    """Raised when the upstream extraction provider fails."""


class DeepSeekExtractor:
    """Extract order fields using the official DeepSeek chat completions API."""

    def __init__(self, settings: Settings) -> None:
        self._api_key = settings.deepseek_api_key
        self._base_url = settings.deepseek_base_url.rstrip("/")
        self._model = settings.deepseek_model
        self._timeout_seconds = settings.deepseek_timeout_seconds
        self._max_retries = settings.deepseek_max_retries

    def extract(self, document: ProcessedPdf) -> ExtractedOrderFields:
        """Call DeepSeek with page images and embedded text context."""
        if not self._api_key:
            raise ExtractionProviderError("DEEPSEEK_API_KEY is not configured")

        content: list[dict[str, Any]] = [
            {
                "type": "text",
                "text": self._build_user_prompt(document),
            }
        ]
        for page in document.pages:
            encoded = base64.b64encode(page.image_png_bytes).decode("ascii")
            content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{encoded}",
                        "detail": "high",
                    },
                }
            )

        payload = {
            "model": self._model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": content},
            ],
        }
        response_json = self._request_with_retries(payload)
        return self._parse_response(response_json)

    def _build_user_prompt(self, document: ProcessedPdf) -> str:
        sections = [
            f"The document has {document.page_count} page(s).",
            "Images of every page are attached in order.",
            "Embedded text extracted from each page follows when available.",
        ]
        for page in document.pages:
            text = page.text if page.text else "[no embedded text on this page]"
            sections.append(f"--- Page {page.page_number} embedded text ---\n{text}")
        sections.append("Return the JSON object now.")
        return "\n\n".join(sections)

    def _request_with_retries(self, payload: dict[str, Any]) -> dict[str, Any]:
        attempts = self._max_retries + 1
        last_error: Exception | None = None
        for attempt in range(attempts):
            try:
                with httpx.Client(timeout=self._timeout_seconds) as client:
                    response = client.post(
                        f"{self._base_url}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self._api_key}",
                            "Content-Type": "application/json",
                        },
                        json=payload,
                    )
                if response.status_code in {408, 429, 500, 502, 503, 504}:
                    raise ExtractionProviderError(
                        f"DeepSeek temporary failure (HTTP {response.status_code})"
                    )
                if response.status_code >= 400:
                    logger.warning(
                        "DeepSeek request failed with status %s",
                        response.status_code,
                    )
                    raise ExtractionProviderError("DeepSeek request failed")
                return response.json()
            except (httpx.TimeoutException, httpx.TransportError, ExtractionProviderError) as exc:
                last_error = exc
                if attempt + 1 >= attempts:
                    break
                logger.warning(
                    "Retrying DeepSeek extraction after transient failure (%s/%s)",
                    attempt + 1,
                    attempts,
                )
        raise ExtractionProviderError("DeepSeek extraction failed") from last_error

    def _parse_response(self, response_json: dict[str, Any]) -> ExtractedOrderFields:
        try:
            choices = response_json["choices"]
            message = choices[0]["message"]
            content = message.get("content")
            if not isinstance(content, str) or not content.strip():
                raise ExtractionProviderError("DeepSeek returned an empty response")
            parsed = _loads_json_object(content)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise ExtractionProviderError("DeepSeek returned a malformed response") from exc

        values: dict[str, str | None] = {}
        for field_name in _FIELD_NAMES:
            raw = parsed.get(field_name, None)
            values[field_name] = _normalize_optional_string(raw)
        return ExtractedOrderFields(**values)


def _normalize_optional_string(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    cleaned = value.strip()
    if not cleaned or cleaned.lower() in {"null", "none", "n/a", "unknown"}:
        return None
    return cleaned


def _loads_json_object(content: str) -> dict[str, Any]:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, flags=re.DOTALL)
        if not match:
            raise
        parsed = json.loads(match.group(0))
    if not isinstance(parsed, dict):
        raise json.JSONDecodeError("Expected a JSON object", content, 0)
    return parsed
