"""
Tests for text cleaning utilities.
"""
from src.preprocessing.text_cleaning import clean_page_text, normalize_whitespace


def test_normalize_whitespace_replaces_nbsp():
    text = "personal\xa0accident\xa0policy"
    assert normalize_whitespace(text) == "personal accident policy"


def test_normalize_whitespace_removes_zero_width_space():
    text = "waived\u200boff"
    assert normalize_whitespace(text) == "waivedoff"


def test_normalize_whitespace_collapses_repeated_spaces():
    text = "room   rent    limit"
    assert normalize_whitespace(text) == "room rent limit"


def test_clean_page_text_strips_leading_trailing_blank_lines():
    text = "\n\n  Policy Schedule  \nRoom Rent\n\n"
    cleaned = clean_page_text(text)
    assert cleaned == "Policy Schedule\nRoom Rent"


def test_clean_page_text_preserves_internal_blank_lines():
    text = "Section A\n\nSection B"
    cleaned = clean_page_text(text)
    assert cleaned == "Section A\n\nSection B"


def test_clean_page_text_handles_nbsp_in_realistic_pdf_extract():
    text = "liberty\xa0group\xa0personal\xa0accident\xa0policy"
    cleaned = clean_page_text(text)
    assert "personal accident" in cleaned
