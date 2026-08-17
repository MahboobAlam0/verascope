from src.classification.document_type import DocumentType
from src.extraction.field_types import (
    CoverageField,
    CoverageStatus,
    Evidence,
    ValueField,
)
from src.extraction.schema import (
    DocumentMetadata,
    GMCPolicyExtraction,
    InsurerAndTPA,
    NonGMCDocument,
    WaitingPeriods,
)
from src.extraction.serialization import to_evidence_json, to_qms_json


def _metadata(doc_type=DocumentType.GMC_POLICY):
    return DocumentMetadata(
        source_filename="test.pdf",
        document_type=doc_type,
        document_type_confidence=1.0,
        page_count=4,
    )


def test_gmc_extraction_builds_with_all_defaults():
    extraction = GMCPolicyExtraction(document_metadata=_metadata())
    assert extraction.insurer_and_tpa.insurer_name.found is False
    assert extraction.maternity.normal_delivery_limit.status == CoverageStatus.NOT_SPECIFIED


def test_non_gmc_document_does_not_require_full_gmc_schema():
    doc = NonGMCDocument(
        document_metadata=_metadata(doc_type=DocumentType.GPA_POLICY),
        reason="Classified as Group Personal Accident policy - GMC schema not applicable.",
    )
    assert doc.document_metadata.document_type == DocumentType.GPA_POLICY
    assert "Personal Accident" in doc.reason


def test_qms_json_strips_all_evidence():
    extraction = GMCPolicyExtraction(
        document_metadata=_metadata(),
        insurer_and_tpa=InsurerAndTPA(
            insurer_name=ValueField(
                value="Niva Bupa Health Insurance",
                found=True,
                evidence=[Evidence(page=1, text="Niva Bupa Health Insurance", chunk_id="c1")],
            )
        ),
    )
    qms = to_qms_json(extraction)
    assert qms["insurer_and_tpa"]["insurer_name"]["value"] == "Niva Bupa Health Insurance"
    assert "evidence" not in qms["insurer_and_tpa"]["insurer_name"]


def test_evidence_json_contains_only_fields_with_evidence():
    extraction = GMCPolicyExtraction(
        document_metadata=_metadata(),
        insurer_and_tpa=InsurerAndTPA(
            insurer_name=ValueField(
                value="Care Health Insurance",
                found=True,
                evidence=[Evidence(page=1, text="Care Health Insurance", chunk_id="c1")],
            ),
            tpa_name=ValueField(found=False),  # no evidence - not found
        ),
    )
    evidence = to_evidence_json(extraction)
    assert "insurer_and_tpa.insurer_name" in evidence
    assert "insurer_and_tpa.tpa_name" not in evidence
    assert evidence["insurer_and_tpa.insurer_name"][0]["page"] == 1


def test_qms_and_evidence_outputs_derive_from_same_object_consistently():
    extraction = GMCPolicyExtraction(
        document_metadata=_metadata(),
        waiting_periods=WaitingPeriods(
            pre_existing_disease=CoverageField(
                status=CoverageStatus.COVERED,
                evidence=[Evidence(page=2, text="Pre-existing diseases are covered", chunk_id="c3")],
            )
        ),
    )
    qms = to_qms_json(extraction)
    evidence = to_evidence_json(extraction)
    assert qms["waiting_periods"]["pre_existing_disease"]["status"] == "covered"
    assert "waiting_periods.pre_existing_disease" in evidence


def test_processing_notes_default_empty_and_can_record_flags():
    extraction = GMCPolicyExtraction(
        document_metadata=_metadata(),
        processing_notes=["Demographic breakdown unavailable: Annexure A not provided."],
    )
    assert len(extraction.processing_notes) == 1
