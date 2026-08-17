"""
Section detection within a page's text (Phase 4).
"""
from __future__ import annotations

import re
from difflib import SequenceMatcher

from pydantic import BaseModel

_NUMBERED_LIST_ITEM_PATTERN = re.compile(r"^(\d+)\.\s+\S")
_NUMBERED_LIST_START_PATTERN = re.compile(r"^1\.\s+\S")

KNOWN_SECTION_NAMES = [
    "waiting period",
    "pre & post hospitalization",
    "maternity",
    "other benefits",
    "details of benefits and optional extensions",
    "ppe kit only covid 19 treatments",
    "other term and conditions",
    "corporate floater sum insured",
]


class DocumentSection(BaseModel):

    page_number: int
    heading_raw: str = ""
    heading_canonical: str | None = None
    body_text: str


def _canonicalize_heading(heading_raw: str, threshold: float = 0.75) -> str | None:
    heading_lower = heading_raw.strip().lower()
    best_match: str | None = None
    best_ratio = 0.0
    for candidate in KNOWN_SECTION_NAMES:
        ratio = SequenceMatcher(None, heading_lower, candidate).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = candidate
    if best_ratio >= threshold:
        return best_match
    return None


def detect_sections(page_text: str, page_number: int) -> list[DocumentSection]:
    lines = [line for line in page_text.split("\n")]

    # Find indices of heading candidate lines.
    heading_indices: list[int] = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or _NUMBERED_LIST_ITEM_PATTERN.match(stripped):
            continue
        # Look ahead to the next non-empty line.
        for j in range(i + 1, len(lines)):
            next_stripped = lines[j].strip()
            if not next_stripped:
                continue
            if _NUMBERED_LIST_START_PATTERN.match(next_stripped):
                heading_indices.append(i)
            break

    sections: list[DocumentSection] = []

    if not heading_indices:
        body = "\n".join(lines).strip()
        if body:
            sections.append(
                DocumentSection(page_number=page_number, heading_raw="", body_text=body)
            )
        return sections

    if heading_indices[0] > 0:
        preamble = "\n".join(lines[: heading_indices[0]]).strip()
        if preamble:
            sections.append(
                DocumentSection(page_number=page_number, heading_raw="", body_text=preamble)
            )

    for idx, heading_line_idx in enumerate(heading_indices):
        heading_raw = lines[heading_line_idx].strip()
        body_start = heading_line_idx + 1
        body_end = (
            heading_indices[idx + 1] if idx + 1 < len(heading_indices) else len(lines)
        )
        body_text = "\n".join(lines[body_start:body_end]).strip()
        sections.append(
            DocumentSection(
                page_number=page_number,
                heading_raw=heading_raw,
                heading_canonical=_canonicalize_heading(heading_raw),
                body_text=body_text,
            )
        )

    return sections
