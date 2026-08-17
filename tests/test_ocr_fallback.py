"""
Tests for the OCR fallback (Phase 3).
"""
from __future__ import annotations

import fitz
from PIL import Image, ImageDraw, ImageFont

from src.ingestion.ocr_fallback import ocr_page
from src.ingestion.pdf_reader import ingest_pdf


def _build_scanned_pdf(tmp_path, text: str) -> str:
    """Build a PDF whose only page is a rendered image (no text layer)."""
    image = Image.new("RGB", (1400, 300), color="white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=48)
    draw.text((30, 100), text, fill="black", font=font)
    image_path = tmp_path / "scanned_page.png"
    image.save(image_path)

    pdf_path = tmp_path / "scanned.pdf"
    doc = fitz.open()
    page = doc.new_page(width=1400, height=300)
    page.insert_image(fitz.Rect(0, 0, 1400, 300), filename=str(image_path))
    doc.save(str(pdf_path))
    doc.close()
    return str(pdf_path)


def test_ocr_page_recovers_text_from_an_image_only_page(tmp_path):
    pdf_path = _build_scanned_pdf(tmp_path, "SAMPLE INSURANCE POLICY")
    text = ocr_page(pdf_path, 0)
    assert "INSURANCE" in text.upper()


def test_ocr_page_returns_empty_string_on_bad_input():
    assert ocr_page("does_not_exist.pdf", 0) == ""


def test_ingest_pdf_triggers_ocr_and_sets_used_ocr_flag(tmp_path):
    pdf_path = _build_scanned_pdf(tmp_path, "GROUP MEDICAL COVER")
    document = ingest_pdf(pdf_path)
    assert document.used_ocr is True
    assert "MEDICAL" in document.pages[0].text.upper()


def test_ingest_pdf_does_not_use_ocr_for_text_native_sample():

    document = ingest_pdf("data/input/1_Policy_Copy.pdf")
    assert document.used_ocr is False
