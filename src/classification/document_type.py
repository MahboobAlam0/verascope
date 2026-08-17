"""
Document-type classification (Pipeline Stage 0).
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel

from src.ingestion.models import IngestedDocument

_GMC_KEYWORDS = [
    "room rent",
    "hospitalization",
    "hospitalisation",
    "maternity",
    "day care",
    "icu",
    "pre-existing disease",
    "waiting period",
    "sum insured",
    "in-patient",
    "inpatient",
    "ambulance",
    "ayush",
    "domiciliary",
    "cashless",
    "opd",
    "network hospital",
    "family floater",
    "pre-hospitalization",
    "post-hospitalization",
    "cataract",
]

_GPA_KEYWORDS = [
    "personal accident",
    "accidental death",
    "permanent total disability",
    "permanent partial disability",
    "temporary total disability",
    "capital sum insured",
    "accidental medical expenses",
    "loss of limb",
    "loss of sight",
    "disappearance",
    "accident policy",
]


class DocumentType(str, Enum):
    GMC_POLICY = "gmc_policy"
    GPA_POLICY = "gpa_policy"
    UNKNOWN = "unknown"


class ClassificationResult(BaseModel):
    document_type: DocumentType
    confidence: float
    gmc_score: int
    gpa_score: int
    reason: str


def classify_document(doc: IngestedDocument) -> ClassificationResult:
    """Classify an ingested document as GMC, GPA, or unknown.
    """
    full_text_lower = doc.full_text().lower()

    gmc_score = sum(1 for kw in _GMC_KEYWORDS if kw in full_text_lower)
    gpa_score = sum(1 for kw in _GPA_KEYWORDS if kw in full_text_lower)

    total = gmc_score + gpa_score
    if total == 0:
        return ClassificationResult(
            document_type=DocumentType.UNKNOWN,
            confidence=0.0,
            gmc_score=gmc_score,
            gpa_score=gpa_score,
            reason="No GMC or GPA indicator keywords found in document text.",
        )

    if gmc_score > gpa_score:
        confidence = gmc_score / total
        return ClassificationResult(
            document_type=DocumentType.GMC_POLICY,
            confidence=round(confidence, 2),
            gmc_score=gmc_score,
            gpa_score=gpa_score,
            reason=(
                f"Matched {gmc_score} GMC indicator terms "
                f"(e.g. room rent, hospitalization, maternity) vs "
                f"{gpa_score} GPA indicator terms."
            ),
        )
    elif gpa_score > gmc_score:
        confidence = gpa_score / total
        return ClassificationResult(
            document_type=DocumentType.GPA_POLICY,
            confidence=round(confidence, 2),
            gmc_score=gmc_score,
            gpa_score=gpa_score,
            reason=(
                f"Matched {gpa_score} GPA indicator terms "
                f"(e.g. accidental death, permanent disability) vs "
                f"{gmc_score} GMC indicator terms. This document does not "
                f"appear to be a Group Medical Cover policy."
            ),
        )
    else:
        return ClassificationResult(
            document_type=DocumentType.UNKNOWN,
            confidence=0.5,
            gmc_score=gmc_score,
            gpa_score=gpa_score,
            reason="Equal GMC and GPA indicator scores; classification ambiguous.",
        )
