"""
Positional table reconstruction (fallback for pdfplumber failures).
"""
from __future__ import annotations

import fitz  # PyMuPDF

from src.ingestion.models import ExtractedTable

_ROW_Y_TOLERANCE = 3.0

_COLUMN_GAP_THRESHOLD = 15.0


_MIN_ROWS_FOR_TABLE = 3


def _cluster_rows(words: list[tuple]) -> list[list[tuple[float, float, str]]]:
    """Group words into rows based on y0 proximity, preserving top-to-bottom order."""
    sorted_words = sorted(words, key=lambda w: w[1])  # sort by y0
    rows: list[list[tuple[float, float, str]]] = []
    current_row: list[tuple[float, float, str]] = []
    current_y: float | None = None

    for w in sorted_words:
        x0, y0, x1, _y1, text = w[0], w[1], w[2], w[3], w[4]
        if current_y is None or abs(y0 - current_y) <= _ROW_Y_TOLERANCE:
            current_row.append((x0, x1, text))
            current_y = y0 if current_y is None else current_y
        else:
            rows.append(current_row)
            current_row = [(x0, x1, text)]
            current_y = y0
    if current_row:
        rows.append(current_row)

    return rows


def _split_row_into_cells(row_words: list[tuple[float, float, str]]) -> list[str]:
    """Split a row's words into cells based on horizontal gaps."""
    sorted_words = sorted(row_words, key=lambda t: t[0])
    cells: list[str] = []
    current_tokens = [sorted_words[0][2]]
    current_end = sorted_words[0][1]

    for x0, x1, text in sorted_words[1:]:
        if x0 - current_end > _COLUMN_GAP_THRESHOLD:
            cells.append(" ".join(current_tokens))
            current_tokens = [text]
        else:
            current_tokens.append(text)
        current_end = x1

    cells.append(" ".join(current_tokens))
    return cells


def reconstruct_positional_table(pdf_path: str, page_index: int) -> ExtractedTable | None:

    doc = fitz.open(pdf_path)
    if page_index >= len(doc):
        doc.close()
        return None

    page = doc[page_index]
    words = page.get_text("words")
    doc.close()

    if not words:
        return None

    row_groups = _cluster_rows(words)
    rows = [_split_row_into_cells(row) for row in row_groups]

    multi_cell_rows = [r for r in rows if len(r) > 1]
    if len(multi_cell_rows) < _MIN_ROWS_FOR_TABLE:
        return None

    return ExtractedTable(table_index=0, rows=rows)
