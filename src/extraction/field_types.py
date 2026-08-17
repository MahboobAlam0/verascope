"""
Reusable field types for the GMC extraction schema (Phase 1).
"""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class CoverageStatus(str, Enum):
    COVERED = "covered"
    NOT_COVERED = "not_covered"
    WAIVED_OFF = "waived_off"
    NOT_SPECIFIED = "not_specified"


class LimitType(str, Enum):
    FLAT_AMOUNT = "flat_amount"       
    PERCENT_OF_SI = "percent_of_si"   
    NO_LIMIT = "no_limit"             
    DAYS = "days"                     


class Limit(BaseModel):
    limit_type: LimitType
    amount: float | None = Field(
        default=None, description="Numeric value; meaning depends on limit_type"
    )
    currency: str | None = Field(default="INR")


class Evidence(BaseModel):
    page: int
    text: str = Field(description="Verbatim supporting text snippet from the source document")
    chunk_id: str | None = None


class ValueField(BaseModel):
    """A plain fact: found or not found, optionally with a value."""

    value: str | float | None = None
    found: bool = False
    evidence: list[Evidence] = Field(default_factory=list)

    @model_validator(mode="after")
    def value_consistent_with_found(self) -> "ValueField":
        if self.found and self.value is None:
            raise ValueError("found=True requires a non-null value")
        if not self.found and self.value is not None:
            raise ValueError("found=False must not carry a value (avoid implying it was extracted)")
        return self


class CoverageField(BaseModel):

    status: CoverageStatus = CoverageStatus.NOT_SPECIFIED
    limit: Limit | None = None
    conditions: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)

    @model_validator(mode="after")
    def limit_only_when_covered(self) -> "CoverageField":
        if self.status in (CoverageStatus.NOT_COVERED, CoverageStatus.NOT_SPECIFIED):
            if self.limit is not None:
                raise ValueError(
                    f"status={self.status.value} must not carry a limit "
                    f"(a limit implies the benefit is at least partially covered)"
                )
        return self
