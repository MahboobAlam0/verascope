import pytest
from pydantic import ValidationError

from src.extraction.field_types import (
    CoverageField,
    CoverageStatus,
    Limit,
    LimitType,
    ValueField,
)


def test_value_field_defaults_to_not_found():
    field = ValueField()
    assert field.found is False
    assert field.value is None


def test_value_field_found_true_requires_value():
    with pytest.raises(ValidationError):
        ValueField(found=True, value=None)


def test_value_field_found_false_rejects_value():
    with pytest.raises(ValidationError):
        ValueField(found=False, value="unexpected")


def test_value_field_valid_found_state():
    field = ValueField(found=True, value="Care Health Insurance Ltd.")
    assert field.found is True
    assert field.value == "Care Health Insurance Ltd."


def test_coverage_field_defaults_to_not_specified():
    field = CoverageField()
    assert field.status == CoverageStatus.NOT_SPECIFIED


def test_coverage_field_not_covered_rejects_limit():
    with pytest.raises(ValidationError):
        CoverageField(
            status=CoverageStatus.NOT_COVERED,
            limit=Limit(limit_type=LimitType.FLAT_AMOUNT, amount=5000),
        )


def test_coverage_field_not_specified_rejects_limit():
    with pytest.raises(ValidationError):
        CoverageField(
            status=CoverageStatus.NOT_SPECIFIED,
            limit=Limit(limit_type=LimitType.FLAT_AMOUNT, amount=5000),
        )


def test_coverage_field_covered_allows_limit():
    field = CoverageField(
        status=CoverageStatus.COVERED,
        limit=Limit(limit_type=LimitType.FLAT_AMOUNT, amount=75000, currency="INR"),
    )
    assert field.limit.amount == 75000


def test_coverage_field_waived_off_allows_no_limit():
    # Waived off means the waiting period doesn't apply - no limit concept here.
    field = CoverageField(status=CoverageStatus.WAIVED_OFF, conditions=["for all members"])
    assert field.limit is None
    assert field.conditions == ["for all members"]
