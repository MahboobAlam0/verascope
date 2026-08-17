"""
Retrieval stage definitions (Phase 6 / Phase 7 staging).
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class ExtractionStage(str, Enum):
    INSURER_AND_TPA = "insurer_and_tpa"
    PREVIOUS_POLICY = "previous_policy"
    POLICY_STRUCTURE_AND_DEMOGRAPHICS = "policy_structure_and_demographics"
    HOSPITALIZATION = "hospitalization"
    MATERNITY = "maternity"
    WAITING_PERIODS = "waiting_periods"
    OTHER_BENEFITS = "other_benefits"
    INFERTILITY_AND_AMBULANCE = "infertility_and_ambulance"
    BUFFER_AND_WAIVERS = "buffer_and_waivers"


class StageRetrievalSpec(BaseModel):
    stage: ExtractionStage
    canonical_headings: list[str] = []
    keywords: list[str] = []
    always_include_first_page: bool = False


STAGE_SPECS: dict[ExtractionStage, StageRetrievalSpec] = {
    ExtractionStage.INSURER_AND_TPA: StageRetrievalSpec(
        stage=ExtractionStage.INSURER_AND_TPA,
        canonical_headings=[],
        keywords=[
            "insurer", "insurance company", "tpa", "third party administrator",
            "policyholder", "insured name", "claims administrator",
            "underwriter", "underwritten by", "issuing office", "administered by",
            "claims processed by", "claims support",
        ],
        always_include_first_page=True,
    ),
    ExtractionStage.PREVIOUS_POLICY: StageRetrievalSpec(
        stage=ExtractionStage.PREVIOUS_POLICY,
        canonical_headings=[],
        keywords=[
            "policy period", "inception", "renewal", "tenure", "premium",
            "policy number", "commencement",
            "policy start date", "policy end date", "effective date",
            "expiry date", "period of insurance", "risk commencement",
        ],
        always_include_first_page=True,
    ),
    ExtractionStage.POLICY_STRUCTURE_AND_DEMOGRAPHICS: StageRetrievalSpec(
        stage=ExtractionStage.POLICY_STRUCTURE_AND_DEMOGRAPHICS,
        canonical_headings=["details of benefits and optional extensions"],
        keywords=[
            "family structure", "employee", "spouse", "dependent", "children",
            "parents", "sum insured", "primary insured", "dependents", "total",
            "category", "grade", "cadre", "headcount", "member count",
            "floater sum insured", "individual sum insured", "no. of members",
        ],
        always_include_first_page=True,
    ),
    ExtractionStage.HOSPITALIZATION: StageRetrievalSpec(
        stage=ExtractionStage.HOSPITALIZATION,
        canonical_headings=["pre & post hospitalization"],
        keywords=[
            "room rent", "icu", "hospitalization", "in-patient", "inpatient", "day care",
            "cashless", "reimbursement", "network hospital", "twin sharing",
            "single private", "deluxe room", "room category", "eligible room rent",
        ],
    ),
    ExtractionStage.MATERNITY: StageRetrievalSpec(
        stage=ExtractionStage.MATERNITY,
        canonical_headings=["maternity"],
        keywords=[
            "maternity", "delivery", "c-section", "lscs", "baby", "natal",
            "vaccination", "vaccine", "metro", "non-metro", "non metro",
            "pregnancy", "newborn", "new born baby", "childbirth", "obstetric",
        ],
    ),
    ExtractionStage.WAITING_PERIODS: StageRetrievalSpec(
        stage=ExtractionStage.WAITING_PERIODS,
        canonical_headings=["waiting period"],
        keywords=[
            "waiting period", "pre-existing", "ped", "waived", "30 days",
            "first year", "second year", "initial waiting",
            "cooling period", "moratorium", "exclusion period",
            "specific disease waiting", "named ailment",
        ],
    ),
    ExtractionStage.OTHER_BENEFITS: StageRetrievalSpec(
        stage=ExtractionStage.OTHER_BENEFITS,
        canonical_headings=["other benefits", "ppe kit only covid 19 treatments"],
        keywords=[
            "opd", "teleconsultation", "day care", "ayush", "bariatric",
            "psychiatric", "domiciliary", "health check", "modern treatment",
            "pharmacy", "pharmacy discount", "lgbtq", "live-in partner",
            "live in partner", "organ donor", "donor",
            "outpatient", "consultation", "diagnostic", "wellness",
            "second opinion", "home care", "e-consultation",
        ],
    ),
    ExtractionStage.INFERTILITY_AND_AMBULANCE: StageRetrievalSpec(
        stage=ExtractionStage.INFERTILITY_AND_AMBULANCE,
        canonical_headings=[],
        keywords=[
            "infertility", "surrogacy", "ambulance", "air ambulance",
            "ivf", "fertility treatment", "road ambulance", "emergency transportation",
        ],
    ),
    ExtractionStage.BUFFER_AND_WAIVERS: StageRetrievalSpec(
        stage=ExtractionStage.BUFFER_AND_WAIVERS,
        canonical_headings=["corporate floater sum insured"],
        keywords=[
            "corporate buffer", "disease-wise capping", "waiver", "corporate floater",
            "aggregate limit", "top-up", "super top up", "sub-limit", "capping",
        ],
    ),
}
