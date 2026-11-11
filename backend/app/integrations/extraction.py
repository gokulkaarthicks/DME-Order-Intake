"""Extraction provider interface and shared extraction result types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.integrations.pdf_processor import ProcessedPdf


@dataclass(frozen=True)
class ExtractedOrderFields:
    """Nullable five-field extraction result from a document model."""

    patient_first_name: str | None
    patient_last_name: str | None
    patient_dob: str | None
    provider_name: str | None
    provider_npi: str | None


class OrderFieldExtractor(Protocol):
    """Replaceable provider interface for multimodal order-field extraction."""

    def extract(self, document: ProcessedPdf) -> ExtractedOrderFields:
        """Extract the five required order fields from a processed PDF."""
