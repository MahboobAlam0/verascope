"""
Contradiction detection (Phase 11).
"""
from __future__ import annotations

import re

from src.extraction.field_types import CoverageField, Evidence, ValueField
from src.extraction.schema import GMCPolicyExtraction

_NUMBER_PATTERN = re.compile(r"\d[\d,]*(?:\.\d+)?")


def _numbers_in_text(text: str) -> set[str]:
    return {m.replace(",", "") for m in _NUMBER_PATTERN.findall(text)}


def _stored_value_numbers(field: ValueField | CoverageField) -> set[str]:
    if isinstance(field, ValueField):
        return _numbers_in_text(str(field.value)) if field.value is not None else set()
    if isinstance(field, CoverageField) and field.limit is not None and field.limit.amount is not None:
        return {str(field.limit.amount)}
    return set()


def _check_field_for_contradiction(field_path: str, field: ValueField | CoverageField) -> list[str]:
    evidence: list[Evidence] = field.evidence
    if len(evidence) < 2:
        return []  # Need at least 2 independent snippets to compare.

    stored_numbers = _stored_value_numbers(field)
    all_evidence_numbers: list[set[str]] = [_numbers_in_text(e.text) for e in evidence]

    non_empty_number_sets = [s for s in all_evidence_numbers if s]
    if len(non_empty_number_sets) >= 2:
        first = non_empty_number_sets[0]
        for other in non_empty_number_sets[1:]:
            if first.isdisjoint(other):
                return [
                    f"Possible contradiction in {field_path}: supporting evidence "
                    f"snippets mention different numeric values ({sorted(first)} vs "
                    f"{sorted(other)}) - flagged for manual review, value not overridden."
                ]
    return []


def detect_contradictions(extraction: GMCPolicyExtraction) -> list[str]:
    """Scan every field with multi-snippet evidence for internal numeric disagreement."""
    notes: list[str] = []
    raw = extraction.model_dump()

    def walk(path: str, value) -> None:
        if isinstance(value, dict):
            if "evidence" in value and ("value" in value or "status" in value):
                # Reconstruct the typed field to reuse the check logic.
                if "status" in value:
                    field = CoverageField.model_validate(value)
                else:
                    field = ValueField.model_validate(value)
                notes.extend(_check_field_for_contradiction(path, field))
            else:
                for k, v in value.items():
                    walk(f"{path}.{k}" if path else k, v)
        elif isinstance(value, list):
            for i, item in enumerate(value):
                walk(f"{path}[{i}]", item)

    walk("", raw)
    return notes
