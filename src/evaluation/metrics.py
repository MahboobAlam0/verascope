"""
Evaluation harness (Phase 12).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel


class FieldEvalResult(BaseModel):
    field_path: str
    expected: Any
    actual: Any
    match: bool


class DocumentEvalReport(BaseModel):
    document: str
    total_fields: int
    matched_fields: int
    accuracy: float
    field_results: list[FieldEvalResult]


def _get_by_dotted_path(data: dict, path: str) -> Any:
    current: Any = data
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def evaluate_document(actual_output: dict, ground_truth: dict[str, Any], document_name: str) -> DocumentEvalReport:
    results = []
    for field_path, expected in ground_truth.items():
        actual = _get_by_dotted_path(actual_output, field_path)
        results.append(
            FieldEvalResult(field_path=field_path, expected=expected, actual=actual, match=(actual == expected))
        )
    matched = sum(1 for r in results if r.match)
    total = len(results)
    return DocumentEvalReport(
        document=document_name,
        total_fields=total,
        matched_fields=matched,
        accuracy=round(matched / total, 3) if total else 0.0,
        field_results=results,
    )


def run_evaluation(output_dir: Path, ground_truth_path: Path) -> list[DocumentEvalReport] | None:
    ground_truth = json.loads(ground_truth_path.read_text())
    ground_truth.pop("_note", None)

    reports = []
    any_found = False
    for doc_name, fields in ground_truth.items():
        stem = Path(doc_name).stem
        output_path = output_dir / f"{stem}.final_output.json"
        if not output_path.exists():
            continue
        any_found = True
        actual = json.loads(output_path.read_text())
        reports.append(evaluate_document(actual, fields, doc_name))

    return reports if any_found else None


if __name__ == "__main__":
    _output_dir = Path("data/output")
    _ground_truth_path = Path(__file__).parent / "ground_truth.json"

    reports = run_evaluation(_output_dir, _ground_truth_path)
    if reports is None:
        print(
            "No final_output.json files found in data/output/. "
            "Run `python run_pipeline.py` with a configured LLM_PROVIDER first, "
            "then re-run this evaluation. No accuracy numbers to report yet - "
            "this is expected, not an error (see README Evaluation section)."
        )
    else:
        for report in reports:
            print(f"{report.document}: {report.matched_fields}/{report.total_fields} "
                f"fields matched ({report.accuracy:.0%})")
            for r in report.field_results:
                if not r.match:
                    print(f"  MISMATCH {r.field_path}: expected={r.expected!r} actual={r.actual!r}")
