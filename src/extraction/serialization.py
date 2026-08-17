"""
Dual serialization: final_output.json (QMS-clean) + evidence.json (Phase 8).
"""
from __future__ import annotations

from typing import Any

from src.extraction.field_types import CoverageField, Evidence, ValueField
from src.extraction.schema import GMCPolicyExtraction


def _strip_evidence(value: Any) -> Any:
    """Recursively convert a model/dict/list, dropping all `evidence` keys."""
    if isinstance(value, (ValueField, CoverageField)):
        data = value.model_dump()
        data.pop("evidence", None)
        return data
    if isinstance(value, dict):
        return {k: _strip_evidence(v) for k, v in value.items() if k != "evidence"}
    if isinstance(value, list):
        return [_strip_evidence(v) for v in value]
    return value


def to_qms_json(extraction: GMCPolicyExtraction) -> dict:
    """Clean output for QMS integration: no evidence, just extracted values."""
    raw = extraction.model_dump()
    return _strip_evidence(raw)


def _collect_evidence(value: Any, path: str, out: dict[str, list[dict]]) -> None:
    if isinstance(value, dict):
        evidence_list = value.get("evidence")
        if isinstance(evidence_list, list) and evidence_list:
            out[path] = evidence_list
        for k, v in value.items():
            if k == "evidence":
                continue
            _collect_evidence(v, f"{path}.{k}" if path else k, out)
    elif isinstance(value, list):
        for i, item in enumerate(value):
            _collect_evidence(item, f"{path}[{i}]", out)


def to_evidence_json(extraction: GMCPolicyExtraction) -> dict:
    raw = extraction.model_dump()
    out: dict[str, list[dict]] = {}
    _collect_evidence(raw, "", out)
    return out
