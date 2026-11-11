"""Coordinate PDF processing, field extraction, validation, and persistence."""

from __future__ import annotations

import hashlib
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import jwt
from pydantic import ValidationError

from app.core.config import Settings
from app.core.npi import is_valid_npi
from app.db.models import User
from app.integrations.deepseek import ExtractionProviderError
from app.integrations.extraction import ExtractedOrderFields, OrderFieldExtractor
from app.integrations.pdf_processor import PDFProcessor, PdfProcessingError
from app.schemas.order import OrderCreate, OrderPublic
from app.services.order_service import OrderService

logger = logging.getLogger(__name__)

_FIELD_NAMES = (
    "patient_first_name",
    "patient_last_name",
    "patient_dob",
    "provider_name",
    "provider_npi",
)


class UploadRejectedError(Exception):
    """Raised for client-fixable upload/PDF problems."""


class ExtractionFailedError(Exception):
    """Raised when extraction infrastructure fails before validation."""


class OrderUploadResult:
    """Typed outcome for PDF upload extraction."""

    def __init__(
        self,
        *,
        status: str,
        saved: bool,
        extracted: ExtractedOrderFields,
        errors: dict[str, str],
        order_id: UUID | None = None,
        order: OrderPublic | None = None,
        review_token: str | None = None,
    ) -> None:
        self.status = status
        self.saved = saved
        self.extracted = extracted
        self.errors = errors
        self.order_id = order_id
        self.order = order
        self.review_token = review_token


class ExtractionService:
    """Orchestrate document intake without owning HTTP or provider SDK details."""

    def __init__(
        self,
        *,
        pdf_processor: PDFProcessor,
        extractor: OrderFieldExtractor,
        order_service: OrderService,
        max_upload_bytes: int,
        settings: Settings,
    ) -> None:
        self._pdf_processor = pdf_processor
        self._extractor = extractor
        self._order_service = order_service
        self._max_upload_bytes = max_upload_bytes
        self._settings = settings

    def process_upload(
        self,
        *,
        user: User,
        file_bytes: bytes,
        filename: str | None,
        content_type: str | None,
        corrections: OrderCreate | None = None,
        review_token: str | None = None,
    ) -> OrderUploadResult:
        """Extract, validate, and optionally persist an order from an uploaded PDF."""
        self._validate_upload(file_bytes=file_bytes, filename=filename, content_type=content_type)

        try:
            document = self._pdf_processor.process(file_bytes)
        except PdfProcessingError as exc:
            raise UploadRejectedError(str(exc)) from exc

        if corrections is not None:
            self._verify_review_token(review_token, user, file_bytes)
            normalized = ExtractedOrderFields(
                patient_first_name=corrections.patient_first_name,
                patient_last_name=corrections.patient_last_name,
                patient_dob=corrections.patient_dob.isoformat(),
                provider_name=corrections.provider_name,
                provider_npi=corrections.provider_npi,
            )
            order = self._order_service.create(user, corrections)
            return OrderUploadResult(
                status="created", saved=True, extracted=normalized, errors={},
                order_id=order.id, order=OrderPublic.model_validate(order),
            )

        try:
            extracted = self._extractor.extract(document)
        except ExtractionProviderError as exc:
            logger.warning("Extraction provider failure for upload")
            raise ExtractionFailedError("Document extraction failed") from exc
        except Exception as exc:
            logger.warning("Unexpected extraction failure for upload")
            raise ExtractionFailedError("Document extraction failed") from exc

        normalized = _normalize_extracted_fields(extracted)
        order_create, errors = _validate_extracted_fields(normalized)
        if order_create is None:
            return OrderUploadResult(
                status="needs_review",
                saved=False,
                extracted=normalized,
                errors=errors,
                review_token=self._create_review_token(user, file_bytes),
            )

        order = self._order_service.create(user, order_create)
        return OrderUploadResult(
            status="created",
            saved=True,
            extracted=normalized,
            errors={},
            order_id=order.id,
            order=OrderPublic.model_validate(order),
        )

    def _create_review_token(self, user: User, file_bytes: bytes) -> str:
        if len(self._settings.jwt_secret_key) < 32:
            raise ExtractionFailedError("Review is unavailable")
        return jwt.encode({
            "review_user": str(user.id),
            "pdf_digest": hashlib.sha256(file_bytes).hexdigest(),
            "purpose": "order_review",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=60),
        }, self._settings.jwt_secret_key, algorithm=self._settings.jwt_algorithm)

    def _verify_review_token(self, token: str | None, user: User, file_bytes: bytes) -> None:
        try:
            claims = jwt.decode(
                token or "", self._settings.jwt_secret_key,
                algorithms=[self._settings.jwt_algorithm],
                options={"require": ["exp", "review_user", "pdf_digest", "purpose"]},
            )
        except jwt.InvalidTokenError as exc:
            raise UploadRejectedError("Invalid or expired review. Upload the PDF again") from exc
        if (claims["purpose"] != "order_review" or claims["review_user"] != str(user.id)
                or claims["pdf_digest"] != hashlib.sha256(file_bytes).hexdigest()):
            raise UploadRejectedError("Review does not match this user and PDF")

    def _validate_upload(
        self,
        *,
        file_bytes: bytes,
        filename: str | None,
        content_type: str | None,
    ) -> None:
        if not file_bytes:
            raise UploadRejectedError("Uploaded file is empty")
        if len(file_bytes) > self._max_upload_bytes:
            raise UploadRejectedError("Uploaded PDF exceeds the maximum allowed size")

        lowered_name = (filename or "").lower()
        lowered_type = (content_type or "").lower()
        looks_like_pdf = (
            lowered_name.endswith(".pdf")
            or "pdf" in lowered_type
            or file_bytes.startswith(b"%PDF")
        )
        if not looks_like_pdf:
            raise UploadRejectedError("Only PDF uploads are supported")
        if not file_bytes.startswith(b"%PDF"):
            raise UploadRejectedError("Uploaded file is not a valid PDF")


def _normalize_extracted_fields(extracted: ExtractedOrderFields) -> ExtractedOrderFields:
    return ExtractedOrderFields(
        patient_first_name=_normalize_name(extracted.patient_first_name),
        patient_last_name=_normalize_name(extracted.patient_last_name),
        patient_dob=_normalize_dob_string(extracted.patient_dob),
        provider_name=_normalize_name(extracted.provider_name),
        provider_npi=_normalize_npi(extracted.provider_npi),
    )


def _normalize_name(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(value.split())
    return cleaned or None


def _normalize_npi(value: str | None) -> str | None:
    if value is None:
        return None
    digits = "".join(character for character in value if character.isdigit())
    return digits or None


def _normalize_dob_string(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    parsed = _parse_dob(cleaned)
    if parsed is None:
        return cleaned
    return parsed.isoformat()


def _parse_dob(value: str) -> date | None:
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%Y/%m/%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _validate_extracted_fields(
    extracted: ExtractedOrderFields,
) -> tuple[OrderCreate | None, dict[str, str]]:
    errors: dict[str, str] = {}
    payload: dict[str, Any] = {}

    for field_name in _FIELD_NAMES:
        value = getattr(extracted, field_name)
        if value is None:
            errors[field_name] = "missing or unreadable"
            continue
        if field_name == "patient_dob":
            parsed = _parse_dob(value)
            if parsed is None:
                errors[field_name] = "invalid date"
                continue
            if parsed > date.today():
                errors[field_name] = "patient_dob cannot be in the future"
                continue
            payload[field_name] = parsed
        elif field_name == "provider_npi":
            if not is_valid_npi(value):
                errors[field_name] = "provider_npi must be a valid 10-digit NPI"
                continue
            payload[field_name] = value
        else:
            payload[field_name] = value

    if errors:
        return None, errors

    try:
        return OrderCreate.model_validate(payload), {}
    except ValidationError as exc:
        return None, _validation_error_map(exc)


def _validation_error_map(exc: ValidationError) -> dict[str, str]:
    mapped: dict[str, str] = {}
    for error in exc.errors():
        location = error.get("loc") or ()
        field_name = str(location[-1]) if location else "order"
        mapped[field_name] = error.get("msg", "invalid value")
    return mapped
