"""
Text cleaning for PDF-extracted text.
"""
from __future__ import annotations

import re
import unicodedata

_WHITESPACE_VARIANTS = {
    "\xa0": " ",  # non-breaking space
    "\u2009": " ",  # thin space
    "\u200a": " ",  # hair space
    "\u200b": "",  # zero-width space (removed, not replaced)
    "\u2028": "\n",  # line separator
}


def normalize_whitespace(text: str) -> str:
    """Replace non-standard whitespace characters with standard equivalents."""
    for variant, replacement in _WHITESPACE_VARIANTS.items():
        text = text.replace(variant, replacement)
    text = re.sub(r"[ \t]+", " ", text)
    return text


def clean_page_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = normalize_whitespace(text)
    lines = [line.strip() for line in text.split("\n")]
    # Trim leading/trailing blank lines only.
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)
