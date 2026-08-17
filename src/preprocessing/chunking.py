"""
Chunking for retrieval (Phase 5).
"""
from __future__ import annotations

from pydantic import BaseModel

from src.ingestion.models import DocumentPage, ExtractedTable, IngestedDocument
from src.preprocessing.structure_detection import DocumentSection, detect_sections


class Chunk(BaseModel):

    chunk_id: str
    page_number: int
    heading_raw: str = ""
    heading_canonical: str | None = None
    body_text: str
    tables: list[ExtractedTable] = []

    def to_context_string(self) -> str:
        parts = []
        if self.heading_raw:
            parts.append(f"## {self.heading_raw}")
        if self.body_text:
            parts.append(self.body_text)
        for table in self.tables:
            md = table.to_markdown()
            if md:
                parts.append(md)
        return "\n\n".join(parts)


def _page_tables(page: DocumentPage) -> list[ExtractedTable]:
    return page.tables


def build_chunks(document: IngestedDocument) -> list[Chunk]:
    chunks: list[Chunk] = []
    chunk_counter = 0

    for page in document.pages:
        sections: list[DocumentSection] = detect_sections(page.text, page.page_number)
        page_tables = _page_tables(page)

        for section in sections:
            chunk_counter += 1
            chunks.append(
                Chunk(
                    chunk_id=f"{document.source_filename}:p{page.page_number}:c{chunk_counter}",
                    page_number=section.page_number,
                    heading_raw=section.heading_raw,
                    heading_canonical=section.heading_canonical,
                    body_text=section.body_text,
                    tables=page_tables,
                )
            )

    return chunks
