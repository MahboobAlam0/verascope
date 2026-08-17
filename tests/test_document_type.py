from src.classification.document_type import DocumentType, classify_document
from src.ingestion.models import DocumentPage, IngestedDocument


def _make_doc(text: str) -> IngestedDocument:
    return IngestedDocument(
        source_filename="test.pdf",
        page_count=1,
        pages=[DocumentPage(page_number=1, text=text, tables=[], char_count=len(text))],
    )


def test_classifies_gmc_policy_correctly():
    doc = _make_doc(
        "Room Rent Sum Insured Hospitalization Maternity Waiting Period ICU Ambulance"
    )
    result = classify_document(doc)
    assert result.document_type == DocumentType.GMC_POLICY
    assert result.confidence == 1.0


def test_classifies_gpa_policy_correctly():
    doc = _make_doc(
        "Personal Accident Accidental Death Permanent Total Disability "
        "Permanent Partial Disability Capital Sum Insured"
    )
    result = classify_document(doc)
    assert result.document_type == DocumentType.GPA_POLICY


def test_unknown_when_no_keywords_present():
    doc = _make_doc("This document contains no relevant insurance terminology at all.")
    result = classify_document(doc)
    assert result.document_type == DocumentType.UNKNOWN
    assert result.confidence == 0.0


def test_gmc_wins_with_more_matched_terms_even_if_gpa_present():
    doc = _make_doc(
        "Room Rent Hospitalization Maternity Waiting Period Sum Insured "
        "Day Care ICU In-patient Ambulance AYUSH Domiciliary "
        "Personal Accident"  # single GPA term shouldn't flip the result
    )
    result = classify_document(doc)
    assert result.document_type == DocumentType.GMC_POLICY
