"""
Prompt templates for each extraction stage (Phase 7).
"""
from __future__ import annotations

_SHARED_SYSTEM_PROMPT = """\
You are extracting structured data from a Group Medical Cover (GMC) insurance \
policy document for an internal Quality Management System. Follow these rules \
strictly:

1. Only extract information that is EXPLICITLY stated in the provided text. \
Never infer, guess, or fill in a plausible-sounding value that is not directly \
supported by the text.
2. If a field's value is not mentioned in the provided text, set found=false \
(for plain facts) or status="not_specified" (for coverage/benefit fields). Do \
NOT confuse "not mentioned" with "not covered" - these are different things.
3. For every field you DO extract, populate its `evidence` list with the exact \
page number (given in the text as [PAGE N] markers) and a verbatim short quote \
supporting the value. Never fabricate a page number or evidence text.
4. For coverage/benefit fields, status must be exactly one of: "covered", \
"not_covered", "waived_off", "not_specified" - never any other value, and \
never a plain yes/no.
5. Preserve monetary limits, percentages, day counts, and conditions exactly \
as stated - do not round or simplify.
6. If a benefit has status "not_covered" or "not_specified", do not populate \
its limit field.

Output must conform exactly to the provided JSON schema.
"""

_STAGE_INSTRUCTIONS: dict[str, str] = {
    "insurer_and_tpa": (
        "Extract the insurer (insurance company) name and, if a distinct "
        "third-party administrator (TPA) is mentioned, its name. Many GMC "
        "policies do not have a separate TPA - the insurer may act as its "
        "own claims administrator. If no distinct TPA is named, set "
        "tpa_name.found=false rather than guessing."
    ),
    "previous_policy": (
        "Extract the policy period start date, end date, tenure, and "
        "inception premium if stated. Normalize dates to YYYY-MM-DD format."
    ),
    "policy_structure_and_demographics": (
        "Extract the family structure description (as stated, e.g. 'Self + "
        "Spouse + 4 Dependent children'), and any demographic counts "
        "(primary insured members, dependents, total lives covered, and if "
        "separately stated: employees, spouses, children, parents, "
        "parents-in-law).\n"
        "For sum_insured_tiers: copy each Sum Insured tier EXACTLY AS WRITTEN "
        "in the source text (e.g. 'Rs. 300,000'), as its own separate string "
        "in the list - do not compute, round, or convert it to a plain "
        "number yourself. If the document lists multiple tiers (e.g. a "
        "'graded' benefit table showing Rs. 300,000 and Rs. 500,000 as "
        "separate options), each tier is its own separate string - never "
        "combine two tiers into one string. Do not include an unrelated "
        "aggregate figure (e.g. a 'Total Sum Insured' shown elsewhere for "
        "the whole group) - only per-member/per-tier amounts belong here."
    ),
    "hospitalization": (
        "Extract room rent coverage (normal and ICU) including percentage "
        "of Sum Insured or flat limits and conditions, plus pre- and "
        "post-hospitalization day counts."
    ),
    "maternity": (
        "Extract: whether the 9-month maternity waiting period is waived or "
        "applied; whether baby-day-one cover is provided; whether vaccination "
        "coverage is provided; normal delivery limit; C-section/LSCS limit. "
        "If the document states a SINGLE limit that applies regardless of "
        "hospital location, populate only normal_delivery_limit / "
        "c_section_limit. If the document gives DIFFERENT limits for Metro "
        "vs Non-Metro locations, populate normal_delivery_limit_metro / "
        "normal_delivery_limit_non_metro (and the equivalent c_section_limit_metro / "
        "c_section_limit_non_metro) instead, leaving the undifferentiated field "
        "not_specified."
    ),
    "waiting_periods": (
        "Extract the status of: the 30-day initial waiting period, the "
        "first/second year exclusion for specific diseases, and the "
        "pre-existing disease (PED) waiting period."
    ),
    "other_benefits": (
        "Extract coverage status and limits/conditions for: day care "
        "expenses, OPD benefit, teleconsultation, pharmacy discount, "
        "domiciliary hospitalization, annual health check-up, modern "
        "treatment, bariatric treatment, psychiatric treatment, AYUSH "
        "treatment, LGBTQ+ coverage, live-in partner coverage, and organ "
        "donor expenses."
    ),
    "infertility_and_ambulance": (
        "Extract coverage status and limits for infertility treatment, "
        "surrogacy (as a distinct benefit from infertility treatment - do "
        "not merge the two even if the document discusses them together), "
        "ambulance charges, and air ambulance charges."
    ),
    "buffer_and_waivers": (
        "Extract the corporate buffer/floater limit (status and amount) "
        "and any disease-wise capping conditions, as a list of strings "
        "capturing each named procedure and its sub-limit."
    ),
}


def build_system_prompt() -> str:
    return _SHARED_SYSTEM_PROMPT


def build_user_prompt(stage_key: str, context: str) -> str:
    instruction = _STAGE_INSTRUCTIONS[stage_key]
    return (
        f"TASK: {instruction}\n\n"
        f"SOURCE TEXT (page markers indicate where each chunk of text was "
        f"found in the original document):\n\n{context}"
    )
