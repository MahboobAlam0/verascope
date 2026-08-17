"""
Deterministic validation (Phase 10).
"""
from __future__ import annotations

from pydantic import BaseModel

from src.extraction.schema import GMCPolicyExtraction
from src.preprocessing.normalization import dates_in_order


class ValidationReport(BaseModel):
    issues: list[str] = []
    missing_required_fields: list[str] = []


def validate_policy_dates(extraction: GMCPolicyExtraction) -> list[str]:
    """Check that previous_policy end date is after start date, if both are found."""
    issues = []
    start = extraction.previous_policy.policy_period_start
    end = extraction.previous_policy.policy_period_end
    if start.found and end.found:
        result = dates_in_order(str(start.value), str(end.value))
        if result is False:
            issues.append(
                f"Policy period end date ({end.value}) is not after start date "
                f"({start.value}) - dates may be mis-extracted or mis-formatted."
            )
        elif result is None:
            issues.append(
                f"Could not compare policy period dates (start={start.value!r}, "
                f"end={end.value!r}) - one or both are not in a recognized date format."
            )
    return issues


def validate_demographics(extraction: GMCPolicyExtraction) -> list[str]:
    issues = []
    d = extraction.demographics
    granular_fields = [d.employees, d.spouses, d.children, d.parents, d.parents_in_law]

    if all(f.found for f in granular_fields) and d.total_lives_covered.found:
        granular_sum = sum(float(f.value) for f in granular_fields)  # type: ignore[arg-type]
        total = float(d.total_lives_covered.value)  # type: ignore[arg-type]
        if granular_sum != total:
            issues.append(
                f"Demographic breakdown sums to {granular_sum} but "
                f"total_lives_covered reports {total} - inconsistent."
            )
    elif d.primary_insured_members.found and d.dependents_total.found and d.total_lives_covered.found:
        computed = float(d.primary_insured_members.value) + float(d.dependents_total.value)  # type: ignore
        total = float(d.total_lives_covered.value)  # type: ignore
        if computed != total:
            issues.append(
                f"Primary insured members ({d.primary_insured_members.value}) + "
                f"dependents ({d.dependents_total.value}) = {computed}, but "
                f"total_lives_covered reports {total} - inconsistent."
            )
    return issues


_IMPLAUSIBLE_SI_TIER_THRESHOLD = 100_000_000  


def validate_sum_insured_tiers(extraction: GMCPolicyExtraction) -> list[str]:

    issues = []
    for tier in extraction.policy_structure.sum_insured_tiers:
        if tier <= 0:
            issues.append(f"Sum Insured tier {tier} is not a positive value.")
        elif tier > _IMPLAUSIBLE_SI_TIER_THRESHOLD:
            issues.append(
                f"Sum Insured tier {tier} exceeds a plausible per-member value "
                f"(> {_IMPLAUSIBLE_SI_TIER_THRESHOLD}) - possible LLM number "
                f"concatenation error; verify against the source document."
            )
    return issues


def find_missing_required_fields(extraction: GMCPolicyExtraction) -> list[str]:

    missing = []
    if not extraction.insurer_and_tpa.insurer_name.found:
        missing.append("insurer_and_tpa.insurer_name")
    if not extraction.insurer_and_tpa.tpa_name.found:
        missing.append("insurer_and_tpa.tpa_name")
    if not extraction.previous_policy.policy_period_start.found:
        missing.append("previous_policy.policy_period_start")
    if not extraction.previous_policy.policy_period_end.found:
        missing.append("previous_policy.policy_period_end")
    if not extraction.demographics.total_lives_covered.found:
        missing.append("demographics.total_lives_covered")
    return missing


def run_all_validations(extraction: GMCPolicyExtraction) -> ValidationReport:
    """Run every deterministic check and return a consolidated report."""
    issues: list[str] = []
    issues.extend(validate_policy_dates(extraction))
    issues.extend(validate_demographics(extraction))
    issues.extend(validate_sum_insured_tiers(extraction))
    missing = find_missing_required_fields(extraction)
    return ValidationReport(issues=issues, missing_required_fields=missing)
