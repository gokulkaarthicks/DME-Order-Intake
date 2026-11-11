"""PDF parsing and page rendering with temporary-resource cleanup."""

from __future__ import annotations

from dataclasses import dataclass

import pymupdf as fitz


class PdfProcessingError(Exception):
    """Raised when a PDF cannot be accepted for extraction."""


@dataclass(frozen=True)
class PdfPageContent:
    """One PDF page with embedded text and a rendered PNG image."""

    page_number: int
    text: str
    image_png_bytes: bytes


@dataclass(frozen=True)
class ProcessedPdf:
    """Processed PDF content prepared for multimodal extraction."""

    page_count: int
    pages: list[PdfPageContent]


class PDFProcessor:
    """Parse PDF bytes, extract text, and render pages as PNG images."""

    def __init__(self, *, max_pages: int, render_dpi: int = 150) -> None:
        self._max_pages = max_pages
        self._render_dpi = render_dpi

    def process(self, pdf_bytes: bytes) -> ProcessedPdf:
        """Process all pages up to the configured limit, then close the document."""
        if not pdf_bytes.startswith(b"%PDF"):
            raise PdfProcessingError("Uploaded file is not a valid PDF")

        document: fitz.Document | None = None
        try:
            document = fitz.open(stream=pdf_bytes, filetype="pdf")
            if document.is_encrypted:
                # Attempt an empty password for owner-restricted but openable files.
                if not document.authenticate(""):
                    raise PdfProcessingError("Encrypted PDFs are not supported")

            page_count = document.page_count
            if page_count < 1:
                raise PdfProcessingError("PDF contains no pages")
            if page_count > self._max_pages:
                raise PdfProcessingError(
                    f"PDF exceeds the maximum of {self._max_pages} pages"
                )

            zoom = self._render_dpi / 72.0
            matrix = fitz.Matrix(zoom, zoom)
            pages: list[PdfPageContent] = []
            for index in range(page_count):
                page = document.load_page(index)
                text = page.get_text("text") or ""
                pixmap = page.get_pixmap(matrix=matrix, alpha=False)
                pages.append(
                    PdfPageContent(
                        page_number=index + 1,
                        text=text.strip(),
                        image_png_bytes=pixmap.tobytes("png"),
                    )
                )

            return ProcessedPdf(page_count=page_count, pages=pages)
        except PdfProcessingError:
            raise
        except Exception as exc:
            raise PdfProcessingError("Unable to process PDF") from exc
        finally:
            if document is not None:
                document.close()
