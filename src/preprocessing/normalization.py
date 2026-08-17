"""
Normalization utilities (Phase 9).
"""
from __future__ import annotations

import re
from datetime import date

from dateutil import parser as date_parser


_LAKH_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*(?:lakh|lac)s?", re.IGNORECASE)
_CRORE_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*crores?", re.IGNORECASE)
_NUMERIC_PATTERN = re.compile(r"[\d,]+(?:\.\d+)?")


def normalize_currency(text: str) -> float | None:
    if not text:
        return None
    cleaned = text.strip()

    lakh_match = _LAKH_PATTERN.search(cleaned)
    if lakh_match:
        return float(lakh_match.group(1)) * 100_000

    crore_match = _CRORE_PATTERN.search(cleaned)
    if crore_match:
        return float(crore_match.group(1)) * 10_000_000

    stripped = re.sub(r"(rs\.?|inr|₹|`)", "", cleaned, flags=re.IGNORECASE)
    match = _NUMERIC_PATTERN.search(stripped)
    if not match:
        return None
    number_str = match.group(0).replace(",", "")
    try:
        return float(number_str)
    except ValueError:
        return None



_PERCENT_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*(?:%|percent)", re.IGNORECASE)


def normalize_percentage(text: str) -> float | None:
    """Convert a percentage string to a plain float (e.g. "2%" -> 2.0)."""
    if not text:
        return None
    match = _PERCENT_PATTERN.search(text)
    if not match:
        return None
    return float(match.group(1))



_WORD_TO_NUMBER = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "fifteen": 15, "twenty": 20, "thirty": 30, "forty": 40,
    "forty-five": 45, "sixty": 60, "ninety": 90,
}

_DAYS_NUMERIC_PATTERN = re.compile(r"(\d+)\s*-?\s*day", re.IGNORECASE)


def normalize_days(text: str) -> int | None:
    """Convert a day-count string to an int number of days."""
    if not text:
        return None
    match = _DAYS_NUMERIC_PATTERN.search(text)
    if match:
        return int(match.group(1))

    lowered = text.lower()
    for word, number in _WORD_TO_NUMBER.items():
        if re.search(rf"\b{re.escape(word)}\b", lowered):
            return number
    return None



_TIME_PREFIX_PATTERN = re.compile(
    r"^\s*(?:\d{1,2}:\d{2}\s*hrs?\s*(?:of)?|midnight|noon)\s*", re.IGNORECASE
)


def normalize_date(text: str) -> str | None:
    if not text:
        return None
    cleaned = _TIME_PREFIX_PATTERN.sub("", text).strip()
    if not cleaned:
        return None
    try:
        parsed = date_parser.parse(cleaned, dayfirst=True, fuzzy=True)
        return parsed.date().isoformat()
    except (ValueError, OverflowError):
        return None


def dates_in_order(start_iso: str | None, end_iso: str | None) -> bool | None:
    """Check that end date is after start date. Returns None if either is missing."""
    if not start_iso or not end_iso:
        return None
    try:
        start = date.fromisoformat(start_iso)
        end = date.fromisoformat(end_iso)
        return end > start
    except ValueError:
        return None


_STATUS_KEYWORDS: list[tuple[str, str]] = [
    ("waived off", "waived_off"),
    ("waived", "waived_off"),
    ("not covered", "not_covered"),
    ("not applicable", "not_covered"),
    ("excluded", "not_covered"),
    ("covered", "covered"),
]


def normalize_coverage_status_text(text: str) -> str:
    if not text:
        return "not_specified"
    lowered = text.lower()
    for keyword, status in _STATUS_KEYWORDS:
        if keyword in lowered:
            return status
    return "not_specified"
