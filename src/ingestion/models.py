"""
Data models for representing an ingested PDF document.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class ExtractedTable(BaseModel):

    table_index: int = Field(description="Index of this table within the page, 0-based")
    rows: list[list[str | None]] = Field(
        description="Table rows; each row is a list of cell values (None for empty cells)"
    )

    def to_markdown(self) -> str:
        """Render the table as a markdown string, useful for LLM prompt context."""
        if not self.rows:
            return ""
        lines = []
        for i, row in enumerate(self.rows):
            cells = [c if c is not None else "" for c in row]
            lines.append("| " + " | ".join(cells) + " |")
            if i == 0:
                lines.append("| " + " | ".join(["---"] * len(cells)) + " |")
        return "\n".join(lines)


class DocumentPage(BaseModel):

    page_number: int = Field(description="1-indexed page number")
    text: str = Field(description="Native extracted text for this page")
    tables: list[ExtractedTable] = Field(default_factory=list)
    char_count: int = Field(description="Length of extracted text, used for OCR-need heuristics")
    image_count: int = Field(default=0, description="Number of embedded images on this page")


class IngestedDocument(BaseModel):
    """Represents a fully ingested PDF document."""

    source_filename: str
    page_count: int
    pages: list[DocumentPage]
    used_ocr: bool = Field(
        default=False,
        description="Whether OCR fallback was triggered for any page in this document",
    )

    def full_text(self) -> str:
        parts = []
        for page in self.pages:
            parts.append(f"[PAGE {page.page_number}]\n{page.text}")
        return "\n\n".join(parts)

    def text_density_ok(self, min_chars_per_page: int = 100) -> bool:
        if not self.pages:
            return False
        low_text_pages = [p for p in self.pages if p.char_count < min_chars_per_page]
        # Flag as insufficient only if a meaningful fraction of pages are low-text.
        return len(low_text_pages) / len(self.pages) < 0.3
