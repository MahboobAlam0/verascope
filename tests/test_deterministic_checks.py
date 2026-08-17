from src.classification.document_type import DocumentType
from src.extraction.field_types import ValueField
from src.extraction.schema import (
    Demographics,
    DocumentMetadata,
    GMCPolicyExtraction,
    PolicyStructure,
    PreviousPolicy,
)
from src.validation.deterministic_checks import (
    find_missing_required_fields,
    run_all_validations,
    validate_demographics,
    validate_policy_dates,
    validate_sum_insured_tiers,
)


def _metadata():
    return DocumentMetadata(
        source_filename="test.pdf",
        document_type=DocumentType.GMC_POLICY,
        document_type_confidence=1.0,
        page_count=4,
    )


def test_validate_policy_dates_passes_when_end_after_start():
    extraction = GMCPolicyExtraction(
        document_metadata=_metadata(),
        previous_policy=PreviousPolicy(
            policy_period_start=ValueField(value="2022-03-17", found=True),
            policy_period_end=ValueField(value="2023-03-16", found=True),
        ),
    )
    assert validate_policy_dates(extraction) == []


def test_validate_policy_dates_flags_end_before_start():
    extraction = GMCPolicyExtraction(
        document_metadata=_metadata(),
        previous_policy=PreviousPolicy(
            policy_period_start=ValueField(value="2023-03-16", found=True),
            policy_period_end=ValueField(value="2022-03-17", found=True),
        ),
    )
    issues = validate_policy_dates(extraction)
    assert len(issues) == 1
    assert "not after start date" in issues[0]


def test_validate_policy_dates_skips_when_dates_missing():
    extraction = GMCPolicyExtraction(document_metadata=_metadata())
    assert validate_policy_dates(extraction) == []


def test_validate_demographics_consistent_totals_pass():
    extraction = GMCPolicyExtraction(
        document_metadata=_metadata(),
        demographics=Demographics(
            primary_insured_members=ValueField(value=86.0, found=True),
            dependents_total=ValueField(value=66.0, found=True),
            total_lives_covered=ValueField(value=152.0, found=True),
        ),
    )
    assert validate_demographics(extraction) == []


def test_validate_demographics_flags_inconsistent_totals():
    extraction = GMCPolicyExtraction(
        document_metadata=_metadata(),
        demographics=Demographics(
            primary_insured_members=ValueField(value=86.0, found=True),
            dependents_total=ValueField(value=66.0, found=True),
            total_lives_covered=ValueField(value=200.0, found=True),
        ),
    )
    issues = validate_demographics(extraction)
    assert len(issues) == 1
    assert "inconsistent" in issues[0]


def test_validate_demographics_noop_when_data_insufficient():
    # This is the EXPECTED case for our sample documents - only partial
    # demographic data is available, so the check should not fire at all.
    extraction = GMCPolicyExtraction(document_metadata=_metadata())
    assert validate_demographics(extraction) == []


def test_validate_sum_insured_tiers_flags_non_positive():
    extraction = GMCPolicyExtraction(
        document_metadata=_metadata(),
        policy_structure=PolicyStructure(sum_insured_tiers=[300000.0, -5.0, 0.0]),
    )
    issues = validate_sum_insured_tiers(extraction)
    assert len(issues) == 2


def test_validate_sum_insured_tiers_flags_implausibly_large_value():
    # Regression test: seen in a real LLM run where two graded SI tiers
    # (300,000 and 500,000) were concatenated into one bogus value
    # (300000500000) instead of two list entries.
    extraction = GMCPolicyExtraction(
        document_metadata=_metadata(),
        policy_structure=PolicyStructure(sum_insured_tiers=[300000500000.0]),
    )
    issues = validate_sum_insured_tiers(extraction)
    assert len(issues) == 1
    assert "plausible" in issues[0]


def test_validate_sum_insured_tiers_accepts_normal_values():
    extraction = GMCPolicyExtraction(
        document_metadata=_metadata(),
        policy_structure=PolicyStructure(sum_insured_tiers=[300000.0, 500000.0, 1000000.0]),
    )
    assert validate_sum_insured_tiers(extraction) == []


def test_find_missing_required_fields_reports_not_found():
    extraction = GMCPolicyExtraction(document_metadata=_metadata())
    missing = find_missing_required_fields(extraction)
    assert "insurer_and_tpa.insurer_name" in missing
    assert "insurer_and_tpa.tpa_name" in missing


def test_run_all_validations_aggregates_everything():
    extraction = GMCPolicyExtraction(
        document_metadata=_metadata(),
        previous_policy=PreviousPolicy(
            policy_period_start=ValueField(value="2023-03-16", found=True),
            policy_period_end=ValueField(value="2022-03-17", found=True),
        ),
    )
    report = run_all_validations(extraction)
    assert len(report.issues) == 1
    assert "insurer_and_tpa.insurer_name" in report.missing_required_fields
