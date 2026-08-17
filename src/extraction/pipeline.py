"""
Full document pipeline.
"""
from __future__ import annotations

from pathlib import Path

from src.classification.document_type import DocumentType, classify_document
from src.extraction.field_types import CoverageField, ValueField
from src.extraction.llm_client import LLMClient
from src.extraction.schema import DocumentMetadata, GMCPolicyExtraction, NonGMCDocument, PolicyStructure
from src.extraction.stage_extractor import (
    PolicyStructureAndDemographics,
    PolicyStructureLLM,
    run_all_stages,
)
from src.ingestion.pdf_reader import ingest_pdf
from src.preprocessing.chunking import build_chunks
from src.preprocessing.normalization import normalize_currency
from src.retrieval.stage_specs import ExtractionStage
from src.validation.contradiction_detection import detect_contradictions
from src.validation.deterministic_checks import run_all_validations


def finalize_policy_structure(llm_structure: PolicyStructureLLM) -> tuple[PolicyStructure, list[str]]:
    notes: list[str] = []
    tiers: list[float] = []
    for raw in llm_structure.sum_insured_tiers:
        value = normalize_currency(raw)
        if value is None:
            notes.append(
                f"policy_structure.sum_insured_tiers: could not parse '{raw}' as a "
                f"number - dropped rather than guessed."
            )
            continue
        if value in tiers:
            continue
        tiers.append(value)
    return (
        PolicyStructure(
            family_structure_description=llm_structure.family_structure_description,
            sum_insured_tiers=tiers,
        ),
        notes,
    )


def process_document(
    pdf_path: str | Path, llm_client: LLMClient
) -> GMCPolicyExtraction | NonGMCDocument:
    pdf_path = Path(pdf_path)

    # Phase 2: ingestion.
    document = ingest_pdf(pdf_path)

    # Stage 0: classification.
    classification = classify_document(document)

    metadata = DocumentMetadata(
        source_filename=document.source_filename,
        document_type=classification.document_type,
        document_type_confidence=classification.confidence,
        page_count=document.page_count,
    )

    if classification.document_type != DocumentType.GMC_POLICY:
        return NonGMCDocument(document_metadata=metadata, reason=classification.reason)

    # Phase 4/5: structure detection + chunking.
    chunks = build_chunks(document)

    # Phase 6/7: retrieval + staged LLM extraction.
    stage_results, extraction_notes = run_all_stages(chunks, llm_client)

    policy_structure_and_demographics = stage_results[
        ExtractionStage.POLICY_STRUCTURE_AND_DEMOGRAPHICS
    ]
    assert isinstance(policy_structure_and_demographics, PolicyStructureAndDemographics)
    policy_structure, si_tier_notes = finalize_policy_structure(
        policy_structure_and_demographics.policy_structure
    )

    extraction = GMCPolicyExtraction(
        document_metadata=metadata,
        insurer_and_tpa=stage_results[ExtractionStage.INSURER_AND_TPA],
        previous_policy=stage_results[ExtractionStage.PREVIOUS_POLICY],
        policy_structure=policy_structure,
        demographics=policy_structure_and_demographics.demographics,
        hospitalization=stage_results[ExtractionStage.HOSPITALIZATION],
        maternity=stage_results[ExtractionStage.MATERNITY],
        waiting_periods=stage_results[ExtractionStage.WAITING_PERIODS],
        other_benefits=stage_results[ExtractionStage.OTHER_BENEFITS],
        infertility_and_ambulance=stage_results[ExtractionStage.INFERTILITY_AND_AMBULANCE],
        buffer_and_waivers=stage_results[ExtractionStage.BUFFER_AND_WAIVERS],
        processing_notes=extraction_notes + si_tier_notes,
    )

    # Phase 10: deterministic validation.
    validation_report = run_all_validations(extraction)
    extraction.processing_notes.extend(validation_report.issues)
    if validation_report.missing_required_fields:
        extraction.processing_notes.append(
            "Missing required fields: " + ", ".join(validation_report.missing_required_fields)
        )

    # Phase 11: contradiction detection.
    extraction.processing_notes.extend(detect_contradictions(extraction))

    return extraction
