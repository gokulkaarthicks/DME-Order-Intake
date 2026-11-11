"""Synthetic PDF builders for extraction tests (no real PHI)."""

from __future__ import annotations

import pymupdf as fitz

from app.integrations.extraction import ExtractedOrderFields


def build_text_pdf(lines: list[str]) -> bytes:
    """Create a digitally generated multi-line PDF."""
    document = fitz.open()
    page = document.new_page()
    y = 72
    for line in lines:
        page.insert_text((72, y), line)
        y += 18
    pdf_bytes = document.tobytes()
    document.close()
    return pdf_bytes


def build_scanned_pdf(lines: list[str]) -> bytes:
    """Create an image-only PDF that mimics a scanned fax page."""
    source = fitz.open()
    source_page = source.new_page()
    y = 72
    for line in lines:
        source_page.insert_text((72, y), line)
        y += 18
    pixmap = source_page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
    source.close()

    scanned = fitz.open()
    page = scanned.new_page(width=pixmap.width, height=pixmap.height)
    page.insert_image(page.rect, pixmap=pixmap)
    pdf_bytes = scanned.tobytes()
    scanned.close()
    return pdf_bytes


def build_multipage_pdf() -> bytes:
    """Create a messy multi-page digital PDF with fields spread across pages."""
    document = fitz.open()
    page1 = document.new_page()
    page1.insert_text((72, 72), "DME ORDER FORM")
    page1.insert_text((72, 100), "Patient First Name: Jane")
    page1.insert_text((72, 120), "Unrelated clinic notes")

    page2 = document.new_page()
    page2.insert_text((72, 72), "Patient Last Name: Doe")
    page2.insert_text((72, 100), "DOB: 1988-04-12")
    page2.insert_text((72, 120), "Consulting physician: Dr. Other")

    page3 = document.new_page()
    page3.insert_text((72, 72), "Ordering Provider: Dr. Example")
    page3.insert_text((72, 100), "Ordering Provider NPI: 1234567893")
    page3.insert_text((72, 120), "Equipment: wheelchair")

    pdf_bytes = document.tobytes()
    document.close()
    return pdf_bytes


VALID_EXTRACTED = ExtractedOrderFields(
    patient_first_name="Jane",
    patient_last_name="Doe",
    patient_dob="1988-04-12",
    provider_name="Dr. Example",
    provider_npi="1234567893",
)

SAMPLE_ORDER_LINES = [
    "Patient: Jane Doe",
    "DOB: 1988-04-12",
    "Ordering Provider: Dr. Example",
    "NPI: 1234567893",
]
