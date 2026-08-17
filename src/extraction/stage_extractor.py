"""
Stage extraction orchestration (Phase 7).
"""
from __future__ import annotations

import logging

from pydantic import BaseModel, Field, ValidationError

from src.extraction.field_types import Evidence, ValueField
from src.extraction.llm_client import LLMClient
from src.extraction.prompts import build_system_prompt, build_user_prompt
from src.extraction.schema import (
    BufferAndWaivers,
    Demographics,
    Hospitalization,
    InfertilityAndAmbulance,
    InsurerAndTPA,
    Maternity,
    OtherBenefits,
    PolicyStructure,
    PreviousPolicy,
    WaitingPeriods,
)
from src.preprocessing.chunking import Chunk
from src.retrieval.retriever import retrieve_chunks_for_stage
from src.retrieval.stage_specs import ExtractionStage

logger = logging.getLogger(__name__)


class PolicyStructureLLM(BaseModel):

    family_structure_description: ValueField = Field(default_factory=ValueField)
    sum_insured_tiers: list[str] = Field(
        default_factory=list,
        description=(
            "Each Sum Insured tier exactly as written in the source text "
            "(e.g. 'Rs. 300,000'), one string per tier."
        ),
    )


class PolicyStructureAndDemographics(BaseModel):

    policy_structure: PolicyStructureLLM = Field(default_factory=PolicyStructureLLM)
    demographics: Demographics = Field(default_factory=Demographics)


_STAGE_TARGET_MODEL: dict[ExtractionStage, type[BaseModel]] = {
    ExtractionStage.INSURER_AND_TPA: InsurerAndTPA,
    ExtractionStage.PREVIOUS_POLICY: PreviousPolicy,
    ExtractionStage.POLICY_STRUCTURE_AND_DEMOGRAPHICS: PolicyStructureAndDemographics,
    ExtractionStage.HOSPITALIZATION: Hospitalization,
    ExtractionStage.MATERNITY: Maternity,
    ExtractionStage.WAITING_PERIODS: WaitingPeriods,
    ExtractionStage.OTHER_BENEFITS: OtherBenefits,
    ExtractionStage.INFERTILITY_AND_AMBULANCE: InfertilityAndAmbulance,
    ExtractionStage.BUFFER_AND_WAIVERS: BufferAndWaivers,
}


def _build_context(chunks: list[Chunk]) -> str:
    parts = []
    seen_tables: set[tuple[int, int]] = set()
    for chunk in chunks:
        section_parts = []
        if chunk.heading_raw:
            section_parts.append(f"## {chunk.heading_raw}")
        if chunk.body_text:
            section_parts.append(chunk.body_text)
        for table in chunk.tables:
            table_key = (chunk.page_number, table.table_index)
            if table_key in seen_tables:
                continue
            seen_tables.add(table_key)
            md = table.to_markdown()
            if md:
                section_parts.append(md)
        parts.append(f"[PAGE {chunk.page_number}]\n" + "\n\n".join(section_parts))
    return "\n\n---\n\n".join(parts)


def run_stage(
    stage: ExtractionStage,
    all_chunks: list[Chunk],
    llm_client: LLMClient,
) -> tuple[BaseModel, list[str]]:
    target_model = _STAGE_TARGET_MODEL[stage]
    notes: list[str] = []

    retrieval_result = retrieve_chunks_for_stage(all_chunks, stage)
    if not retrieval_result.chunks:
        notes.append(
            f"Stage '{stage.value}': no relevant chunks retrieved - "
            f"returning all-default (not found/not specified) values."
        )
        return target_model(), notes

    context = _build_context(retrieval_result.chunks)
    system_prompt = build_system_prompt()
    user_prompt = build_user_prompt(stage.value, context)
    json_schema = target_model.model_json_schema()

    try:
        raw = llm_client.extract_structured(system_prompt, user_prompt, json_schema)
    except Exception as exc:  # noqa: BLE001 - any provider/network failure lands here
        logger.warning("Stage '%s' LLM call failed: %s", stage.value, exc)
        summary = str(exc).splitlines()[0][:200]
        notes.append(f"Stage '{stage.value}': LLM call failed ({summary}); using default values.")
        return target_model(), notes

    try:
        result = target_model.model_validate(raw)
    except ValidationError as exc:
        logger.warning("Stage '%s' LLM output failed schema validation: %s", stage.value, exc)
        notes.append(
            f"Stage '{stage.value}': LLM output failed schema validation "
            f"({exc.error_count()} error(s)); using default values rather than "
            f"risking an inconsistent or hallucinated state."
        )
        return target_model(), notes

    return result, notes


def run_all_stages(
    all_chunks: list[Chunk], llm_client: LLMClient
) -> tuple[dict[ExtractionStage, BaseModel], list[str]]:
    """Run every extraction stage and collect results + aggregated processing notes."""
    results: dict[ExtractionStage, BaseModel] = {}
    all_notes: list[str] = []
    for stage in ExtractionStage:
        result, notes = run_stage(stage, all_chunks, llm_client)
        results[stage] = result
        all_notes.extend(notes)
    return results, all_notes
