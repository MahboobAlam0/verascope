"""
OCR fallback for scanned/image-only PDF pages (Phase 3).
"""
from __future__ import annotations

import io
import logging
import shutil
from pathlib import Path

import fitz  # PyMuPDF
import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)

_WINDOWS_DEFAULT_TESSERACT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def _configure_tesseract_cmd() -> None:
    if shutil.which("tesseract"):
        return
    if Path(_WINDOWS_DEFAULT_TESSERACT).exists():
        pytesseract.pytesseract.tesseract_cmd = _WINDOWS_DEFAULT_TESSERACT


_configure_tesseract_cmd()


def ocr_page(pdf_path: str, page_index: int, dpi: int = 300) -> str:
    try:
        doc = fitz.open(pdf_path)
        try:
            page = doc[page_index]
            pixmap = page.get_pixmap(dpi=dpi)
            image = Image.open(io.BytesIO(pixmap.tobytes("png")))
            return pytesseract.image_to_string(image).strip()
        finally:
            doc.close()
    except Exception as exc:  # noqa: BLE001 - OCR failure must not crash ingestion
        logger.warning("OCR failed for %s page %d: %s", pdf_path, page_index + 1, exc)
        return ""
