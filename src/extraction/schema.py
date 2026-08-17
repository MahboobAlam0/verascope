"""
Top-level extraction schema for GMC policy documents (Phase 1).
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from src.classification.document_type import DocumentType
from src.extraction.field_types import CoverageField, ValueField


class DocumentMetadata(BaseModel):
    source_filename: str
    document_type: DocumentType
    document_type_confidence: float
    page_count: int


class InsurerAndTPA(BaseModel):
    insurer_name: ValueField = Field(default_factory=ValueField)
    tpa_name: ValueField = Field(
        default_factory=ValueField,
        description=(
            "Third-party administrator, if distinct from the insurer. In our "
            "sample set, no document has a TPA separate from the insurer "
            "itself (see Document Analysis Report, item 7) - found=False is "
            "the CORRECT and expected output for these documents, not a bug."
        ),
    )


class PreviousPolicy(BaseModel):
    policy_period_start: ValueField = Field(default_factory=ValueField)
    policy_period_end: ValueField = Field(default_factory=ValueField)
    policy_tenure: ValueField = Field(default_factory=ValueField)
    inception_premium: ValueField = Field(default_factory=ValueField)


class PolicyStructure(BaseModel):
    family_structure_description: ValueField = Field(
        default_factory=ValueField,
        description="Free-text as stated, e.g. 'Self + Spouse + 4 Dependent children'",
    )
    sum_insured_tiers: list[float] = Field(default_factory=list)


class Demographics(BaseModel):
    primary_insured_members: ValueField = Field(default_factory=ValueField)
    dependents_total: ValueField = Field(default_factory=ValueField)
    total_lives_covered: ValueField = Field(default_factory=ValueField)
    # Granular breakdown - see module docstring on why these are optional.
    employees: ValueField = Field(default_factory=ValueField)
    spouses: ValueField = Field(default_factory=ValueField)
    children: ValueField = Field(default_factory=ValueField)
    parents: ValueField = Field(default_factory=ValueField)
    parents_in_law: ValueField = Field(default_factory=ValueField)


class RoomRentAndICU(BaseModel):
    room_rent_normal: CoverageField = Field(default_factory=CoverageField)
    room_rent_icu: CoverageField = Field(default_factory=CoverageField)


class Hospitalization(BaseModel):
    room_rent: RoomRentAndICU = Field(default_factory=RoomRentAndICU)
    pre_hospitalization_days: ValueField = Field(default_factory=ValueField)
    post_hospitalization_days: ValueField = Field(default_factory=ValueField)


class Maternity(BaseModel):
    waiting_period_9_month: CoverageField = Field(default_factory=CoverageField)
    baby_day_one_cover: CoverageField = Field(default_factory=CoverageField)
    vaccination_coverage: CoverageField = Field(default_factory=CoverageField)

    normal_delivery_limit: CoverageField = Field(default_factory=CoverageField)
    normal_delivery_limit_metro: CoverageField = Field(default_factory=CoverageField)
    normal_delivery_limit_non_metro: CoverageField = Field(default_factory=CoverageField)
    c_section_limit: CoverageField = Field(default_factory=CoverageField)
    c_section_limit_metro: CoverageField = Field(default_factory=CoverageField)
    c_section_limit_non_metro: CoverageField = Field(default_factory=CoverageField)


class WaitingPeriods(BaseModel):
    initial_30_day: CoverageField = Field(default_factory=CoverageField)
    first_second_year: CoverageField = Field(default_factory=CoverageField)
    pre_existing_disease: CoverageField = Field(default_factory=CoverageField)


class OtherBenefits(BaseModel):
    day_care: CoverageField = Field(default_factory=CoverageField)
    opd: CoverageField = Field(default_factory=CoverageField)
    teleconsultation: CoverageField = Field(default_factory=CoverageField)
    pharmacy_discount: CoverageField = Field(default_factory=CoverageField)
    domiciliary_hospitalization: CoverageField = Field(default_factory=CoverageField)
    annual_health_checkup: CoverageField = Field(default_factory=CoverageField)
    modern_treatment: CoverageField = Field(default_factory=CoverageField)
    bariatric_treatment: CoverageField = Field(default_factory=CoverageField)
    psychiatric_treatment: CoverageField = Field(default_factory=CoverageField)
    ayush_treatment: CoverageField = Field(default_factory=CoverageField)
    lgbtq_coverage: CoverageField = Field(default_factory=CoverageField)
    live_in_partner_coverage: CoverageField = Field(default_factory=CoverageField)
    organ_donor_expenses: CoverageField = Field(default_factory=CoverageField)


class InfertilityAndAmbulance(BaseModel):
    infertility_treatment: CoverageField = Field(default_factory=CoverageField)
    surrogacy: CoverageField = Field(default_factory=CoverageField)
    ambulance: CoverageField = Field(default_factory=CoverageField)
    air_ambulance: CoverageField = Field(default_factory=CoverageField)


class BufferAndWaivers(BaseModel):
    corporate_buffer_limit: CoverageField = Field(default_factory=CoverageField)
    disease_wise_capping: list[str] = Field(default_factory=list)


class GMCPolicyExtraction(BaseModel):
    document_metadata: DocumentMetadata
    insurer_and_tpa: InsurerAndTPA = Field(default_factory=InsurerAndTPA)
    previous_policy: PreviousPolicy = Field(default_factory=PreviousPolicy)
    policy_structure: PolicyStructure = Field(default_factory=PolicyStructure)
    demographics: Demographics = Field(default_factory=Demographics)
    hospitalization: Hospitalization = Field(default_factory=Hospitalization)
    maternity: Maternity = Field(default_factory=Maternity)
    waiting_periods: WaitingPeriods = Field(default_factory=WaitingPeriods)
    other_benefits: OtherBenefits = Field(default_factory=OtherBenefits)
    infertility_and_ambulance: InfertilityAndAmbulance = Field(
        default_factory=InfertilityAndAmbulance
    )
    buffer_and_waivers: BufferAndWaivers = Field(default_factory=BufferAndWaivers)
    processing_notes: list[str] = Field(default_factory=list)


class NonGMCDocument(BaseModel):
    document_metadata: DocumentMetadata
    reason: str
