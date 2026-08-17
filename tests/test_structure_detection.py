from src.preprocessing.structure_detection import detect_sections


def test_detects_heading_before_numbered_list():
    text = "Maternity\n1. Maximum limit is Rs 75,000.\n2. Payable for first two children only."
    sections = detect_sections(text, page_number=2)
    assert len(sections) == 1
    assert sections[0].heading_raw == "Maternity"
    assert sections[0].heading_canonical == "maternity"


def test_does_not_misdetect_wrapped_continuation_line_as_heading():

    text = (
        "6. The Insured must inform of new additions within a reasonable time "
        "but not later than 30 days from the date of joining the organization. "
        "On exit of employees, deletion should be informed in writing failing "
        "which the liability incurred on claims of\n"
        "such employees after their exit, would be of the employer.\n"
        "7. Domiciliary Hospitalization is specifically excluded."
    )
    sections = detect_sections(text, page_number=3)
    headings = [s.heading_raw for s in sections if s.heading_raw]
    assert "such employees after their exit, would be of the employer." not in headings


def test_multiple_sections_split_correctly_with_boundaries():
    text = (
        "Waiting Period\n"
        "1. PED covered.\n"
        "2. 30 day wait waived.\n"
        "Maternity\n"
        "1. Normal delivery Rs 50,000.\n"
    )
    sections = detect_sections(text, page_number=2)
    assert [s.heading_raw for s in sections] == ["Waiting Period", "Maternity"]
    assert "PED covered" in sections[0].body_text
    assert "30 day wait" in sections[0].body_text
    assert "Maternity" not in sections[0].body_text
    assert "Normal delivery" in sections[1].body_text


def test_canonicalization_handles_typo_via_fuzzy_match():
    text = "Waitin g Period\n1. Something is covered."
    sections = detect_sections(text, page_number=2)
    assert sections[0].heading_canonical == "waiting period"


def test_preamble_before_first_heading_is_preserved():
    text = "Some intro table text.\nMore intro text.\nMaternity\n1. Covered.\n"
    sections = detect_sections(text, page_number=2)
    assert sections[0].heading_raw == ""
    assert "intro table text" in sections[0].body_text
    assert sections[1].heading_raw == "Maternity"


def test_no_numbered_lists_returns_single_untitled_section():
    text = "Just plain prose with no numbered benefit lists at all."
    sections = detect_sections(text, page_number=1)
    assert len(sections) == 1
    assert sections[0].heading_raw == ""


def test_empty_page_returns_no_sections():
    assert detect_sections("", page_number=1) == []
    assert detect_sections("   \n\n  ", page_number=1) == []
