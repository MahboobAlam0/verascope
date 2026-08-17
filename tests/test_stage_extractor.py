from typing import Any, cast

from src.extraction.llm_client import LLMClient
from src.extraction.stage_extractor import _build_context, run_stage
from src.ingestion.models import ExtractedTable
from src.preprocessing.chunking import Chunk
from src.retrieval.stage_specs import ExtractionStage


class FakeLLMClient(LLMClient):
    """Returns a fixed response or raises, for testing orchestration logic
    without any real network call."""

    def __init__(self, response: dict[str, Any] | None = None, raise_exc: Exception | None = None):
        self._response = response
        self._raise_exc = raise_exc

    def extract_structured(self, system_prompt, user_prompt, json_schema) -> dict[str, Any]:
        if self._raise_exc:
            raise self._raise_exc
        return self._response if self._response is not None else {}


def _chunk(chunk_id, page, heading_raw="Maternity", heading_canonical="maternity", body_text="1. Covered."):
    return Chunk(
        chunk_id=chunk_id, page_number=page, heading_raw=heading_raw,
        heading_canonical=heading_canonical, body_text=body_text, tables=[],
    )


def test_build_context_does_not_duplicate_a_shared_page_table():
    table = ExtractedTable(table_index=0, rows=[["Room Rent", "2% of SI"]])
    chunks = [
        Chunk(chunk_id="c1", page_number=3, heading_raw="", body_text="Intro text.", tables=[table]),
        Chunk(chunk_id="c2", page_number=3, heading_raw="Sub-limit", body_text="Sub-limit text.", tables=[table]),
        Chunk(chunk_id="c3", page_number=3, heading_raw="Conditions", body_text="Conditions text.", tables=[table]),
    ]
    context = _build_context(chunks)
    assert context.count("Room Rent") == 1
    assert "Intro text." in context
    assert "Sub-limit text." in context
    assert "Conditions text." in context


def test_build_context_keeps_distinct_tables_from_different_pages():
    table_p1 = ExtractedTable(table_index=0, rows=[["Room Rent", "2% of SI"]])
    table_p2 = ExtractedTable(table_index=0, rows=[["ICU", "4% of SI"]])
    chunks = [
        Chunk(chunk_id="c1", page_number=1, heading_raw="", body_text="Page 1.", tables=[table_p1]),
        Chunk(chunk_id="c2", page_number=2, heading_raw="", body_text="Page 2.", tables=[table_p2]),
    ]
    context = _build_context(chunks)
    assert "Room Rent" in context
    assert "ICU" in context


def test_run_stage_success_path_returns_validated_model():
    chunks = [_chunk("c1", 2)]
    client = FakeLLMClient(response={
        "waiting_period_9_month": {"status": "waived_off", "conditions": [], "evidence": []},
        "baby_day_one_cover": {"status": "not_specified", "conditions": [], "evidence": []},
        "normal_delivery_limit": {"status": "not_specified", "conditions": [], "evidence": []},
        "c_section_limit": {"status": "not_specified", "conditions": [], "evidence": []},
    })
    result, notes = run_stage(ExtractionStage.MATERNITY, chunks, client)
    model = cast(Any, result)
    assert model.waiting_period_9_month.status.value == "waived_off"
    assert notes == []


def test_run_stage_no_chunks_returns_default_with_note():
    result, notes = run_stage(ExtractionStage.MATERNITY, [], FakeLLMClient(response={}))
    model = cast(Any, result)
    assert model.waiting_period_9_month.status.value == "not_specified"
    assert len(notes) == 1
    assert "no relevant chunks" in notes[0]


def test_run_stage_llm_failure_falls_back_gracefully():
    chunks = [_chunk("c1", 2)]
    client = FakeLLMClient(raise_exc=RuntimeError("API timeout"))
    result, notes = run_stage(ExtractionStage.MATERNITY, chunks, client)
    model = cast(Any, result)
    assert model.waiting_period_9_month.status.value == "not_specified"
    assert len(notes) == 1
    assert "LLM call failed" in notes[0]


def test_run_stage_llm_failure_falls_back_gracefully_for_combined_stage():

    chunks = [_chunk("c1", 2, heading_raw="Details", heading_canonical="details of benefits and optional extensions")]
    client = FakeLLMClient(raise_exc=RuntimeError("API error"))
    result, notes = run_stage(ExtractionStage.POLICY_STRUCTURE_AND_DEMOGRAPHICS, chunks, client)
    model = cast(Any, result)
    assert model.policy_structure.sum_insured_tiers == []
    assert model.demographics.total_lives_covered.found is False
    assert len(notes) == 1
    assert "LLM call failed" in notes[0]


def test_run_stage_invalid_llm_output_falls_back_gracefully():
    chunks = [_chunk("c1", 2)]
    client = FakeLLMClient(response={
        "waiting_period_9_month": {
            "status": "not_covered",
            "limit": {"limit_type": "flat_amount", "amount": 5000},
            "conditions": [], "evidence": [],
        },
        "baby_day_one_cover": {"status": "not_specified", "conditions": [], "evidence": []},
        "normal_delivery_limit": {"status": "not_specified", "conditions": [], "evidence": []},
        "c_section_limit": {"status": "not_specified", "conditions": [], "evidence": []},
    })
    result, notes = run_stage(ExtractionStage.MATERNITY, chunks, client)
    model = cast(Any, result)
    assert model.waiting_period_9_month.status.value == "not_specified"  # safe default, not the bad value
    assert len(notes) == 1
    assert "schema validation" in notes[0]
