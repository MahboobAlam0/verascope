"""
Tests for src/extraction/pipeline.py's deterministic post-LLM conversion.
"""
from __future__ import annotations

from src.extraction.field_types import ValueField
from src.extraction.pipeline import finalize_policy_structure
from src.extraction.stage_extractor import PolicyStructureLLM


def test_finalize_policy_structure_parses_each_tier():
    llm_structure = PolicyStructureLLM(
        family_structure_description=ValueField(value="Self + Spouse", found=True),
        sum_insured_tiers=["Rs. 300,000", "Rs. 500,000"],
    )
    result, _ = finalize_policy_structure(llm_structure)
    assert result.sum_insured_tiers == [300000.0, 500000.0]
    assert result.family_structure_description.value == "Self + Spouse"


def test_finalize_policy_structure_drops_unparseable_tier_with_a_note():
    llm_structure = PolicyStructureLLM(sum_insured_tiers=["Rs. 300,000", "not a number"])
    result, notes = finalize_policy_structure(llm_structure)
    assert result.sum_insured_tiers == [300000.0]
    assert len(notes) == 1
    assert "not a number" in notes[0]


def test_finalize_policy_structure_handles_empty_tiers():
    result, _ = finalize_policy_structure(PolicyStructureLLM())
    assert result.sum_insured_tiers == []


def test_finalize_policy_structure_never_recombines_a_single_merged_string():

    llm_structure = PolicyStructureLLM(sum_insured_tiers=["Rs. 300,000 Rs. 500,000"])
    result, notes = finalize_policy_structure(llm_structure)
    assert result.sum_insured_tiers == [300000.0]


def test_finalize_policy_structure_collapses_duplicate_tier_values():

    llm_structure = PolicyStructureLLM(
        sum_insured_tiers=["Rs. 300,000", "Rs. 500,000", "300000", "500000"]
    )
    result, notes = finalize_policy_structure(llm_structure)
    assert result.sum_insured_tiers == [300000.0, 500000.0]
    assert notes == []
