from src.classification.document_type import DocumentType
from src.extraction.field_types import Evidence, ValueField
from src.extraction.schema import DocumentMetadata, GMCPolicyExtraction, InsurerAndTPA
from src.validation.contradiction_detection import detect_contradictions


def _metadata():
    return DocumentMetadata(
        source_filename="test.pdf",
        document_type=DocumentType.GMC_POLICY,
        document_type_confidence=1.0,
        page_count=4,
    )


def test_no_contradiction_with_single_evidence_snippet():
    extraction = GMCPolicyExtraction(
        document_metadata=_metadata(),
        insurer_and_tpa=InsurerAndTPA(
            insurer_name=ValueField(
                value="Care Health Insurance",
                found=True,
                evidence=[Evidence(page=1, text="Care Health Insurance Ltd.", chunk_id="c1")],
            )
        ),
    )
    assert detect_contradictions(extraction) == []


def test_no_contradiction_when_evidence_numbers_agree():
    extraction = GMCPolicyExtraction(
        document_metadata=_metadata(),
        insurer_and_tpa=InsurerAndTPA(
            tpa_name=ValueField(
                value="500000",
                found=True,
                evidence=[
                    Evidence(page=1, text="Sum Insured Rs. 500000", chunk_id="c1"),
                    Evidence(page=2, text="SI: 500000", chunk_id="c2"),
                ],
            )
        ),
    )
    assert detect_contradictions(extraction) == []


def test_flags_contradiction_when_evidence_numbers_disagree():
    extraction = GMCPolicyExtraction(
        document_metadata=_metadata(),
        insurer_and_tpa=InsurerAndTPA(
            tpa_name=ValueField(
                value="75000",
                found=True,
                evidence=[
                    Evidence(page=2, text="Maternity limit Rs. 75,000", chunk_id="c6"),
                    Evidence(page=3, text="Annexure states maternity limit Rs. 50,000", chunk_id="c9"),
                ],
            )
        ),
    )
    notes = detect_contradictions(extraction)
    assert len(notes) == 1
    assert "contradiction" in notes[0].lower()


def test_no_contradiction_when_no_evidence_present():
    extraction = GMCPolicyExtraction(document_metadata=_metadata())
    assert detect_contradictions(extraction) == []
