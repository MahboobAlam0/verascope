"""
PDF ingestion: native text + table extraction.
"""
from __future__ import annotations

import logging
from pathlib import Path

import fitz  # PyMuPDF
import pdfplumber

from src.ingestion.models import DocumentPage, ExtractedTable, IngestedDocument
from src.ingestion.ocr_fallback import ocr_page
from src.ingestion.positional_table_reconstruction import reconstruct_positional_table
from src.preprocessing.text_cleaning import clean_page_text

logger = logging.getLogger(__name__)


def _extract_tables_for_page(pdf_path: str, page_index: int) -> list[ExtractedTable]:

    tables: list[ExtractedTable] = []
    with pdfplumber.open(pdf_path) as pdf:
        if page_index >= len(pdf.pages):
            return tables
        page = pdf.pages[page_index]
        raw_tables = page.extract_tables()
        for i, raw_table in enumerate(raw_tables):
            tables.append(ExtractedTable(table_index=i, rows=raw_table))
    return tables


def ingest_pdf(pdf_path: str | Path) -> IngestedDocument:

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    try:
        doc = fitz.open(str(pdf_path))
    except Exception as exc:  
        raise ValueError(f"Failed to open PDF {pdf_path}: {exc}") from exc

    pages: list[DocumentPage] = []
    for i, page in enumerate(doc):
        text = clean_page_text(page.get_text())
        images = page.get_images()
        tables = _extract_tables_for_page(str(pdf_path), i)

        if not tables:
            positional_table = reconstruct_positional_table(str(pdf_path), i)
            if positional_table is not None:
                tables = [positional_table]
                logger.info(
                    "%s page %d: recovered a table via positional reconstruction "
                    "(pdfplumber found none)",
                    pdf_path.name,
                    i + 1,
                )

        pages.append(
            DocumentPage(
                page_number=i + 1,
                text=text,
                tables=tables,
                char_count=len(text),
                image_count=len(images),
            )
        )

    doc.close()

    ingested = IngestedDocument(
        source_filename=pdf_path.name,
        page_count=len(pages),
        pages=pages,
    )

    if not ingested.text_density_ok():
        logger.warning(
            "%s: low text density detected across pages; running OCR fallback",
            pdf_path.name,
        )
        ocr_pages = _apply_ocr_fallback(str(pdf_path), pages)
        ingested = IngestedDocument(
            source_filename=pdf_path.name,
            page_count=len(ocr_pages),
            pages=ocr_pages,
            used_ocr=True,
        )

    return ingested


def _apply_ocr_fallback(
    pdf_path: str, pages: list[DocumentPage], min_chars_per_page: int = 100
) -> list[DocumentPage]:
    updated: list[DocumentPage] = []
    for page in pages:
        if page.char_count >= min_chars_per_page:
            updated.append(page)
            continue

        ocr_text = clean_page_text(ocr_page(pdf_path, page.page_number - 1))
        if len(ocr_text) > page.char_count:
            logger.info(
                "%s page %d: OCR recovered %d chars (native extraction found %d)",
                pdf_path, page.page_number, len(ocr_text), page.char_count,
            )
            updated.append(page.model_copy(update={"text": ocr_text, "char_count": len(ocr_text)}))
        else:
            updated.append(page)
    return updated
