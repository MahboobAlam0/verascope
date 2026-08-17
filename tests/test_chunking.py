from src.ingestion.models import DocumentPage, ExtractedTable, IngestedDocument
from src.preprocessing.chunking import build_chunks


def test_build_chunks_creates_one_chunk_per_section():
    page = DocumentPage(
        page_number=1,
        text="Maternity\n1. Covered up to Rs 50,000.\nOther Benefits\n1. Ambulance covered.",
        tables=[],
        char_count=100,
    )
    doc = IngestedDocument(source_filename="test.pdf", page_count=1, pages=[page])
    chunks = build_chunks(doc)
    assert len(chunks) == 2
    assert chunks[0].heading_raw == "Maternity"
    assert chunks[1].heading_raw == "Other Benefits"


def test_chunk_attaches_page_level_tables():
    table = ExtractedTable(table_index=0, rows=[["A", "B"], ["1", "2"]])
    page = DocumentPage(
        page_number=1,
        text="Room Rent\n1. Covered up to Rs 2 Lakh.",
        tables=[table],
        char_count=50,
    )
    doc = IngestedDocument(source_filename="test.pdf", page_count=1, pages=[page])
    chunks = build_chunks(doc)
    assert len(chunks) == 1
    assert len(chunks[0].tables) == 1
    assert chunks[0].tables[0].rows == [["A", "B"], ["1", "2"]]


def test_chunk_ids_are_unique_across_pages():
    page1 = DocumentPage(
        page_number=1, text="Maternity\n1. Covered.", tables=[], char_count=20
    )
    page2 = DocumentPage(
        page_number=2, text="Other Benefits\n1. Ambulance covered.", tables=[], char_count=30
    )
    doc = IngestedDocument(source_filename="test.pdf", page_count=2, pages=[page1, page2])
    chunks = build_chunks(doc)
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids))


def test_to_context_string_includes_heading_body_and_tables():
    table = ExtractedTable(table_index=0, rows=[["Limit", "Rs 50,000"]])
    page = DocumentPage(
        page_number=1,
        text="Maternity\n1. Normal delivery covered.",
        tables=[table],
        char_count=40,
    )
    doc = IngestedDocument(source_filename="test.pdf", page_count=1, pages=[page])
    chunks = build_chunks(doc)
    context = chunks[0].to_context_string()
    assert "Maternity" in context
    assert "Normal delivery covered" in context
    assert "Rs 50,000" in context


def test_preamble_chunk_has_no_heading_but_is_retained():
    page = DocumentPage(
        page_number=1,
        text="Policy No: 12345\nInsurer: Example Insurance\nMaternity\n1. Covered.",
        tables=[],
        char_count=60,
    )
    doc = IngestedDocument(source_filename="test.pdf", page_count=1, pages=[page])
    chunks = build_chunks(doc)
    assert chunks[0].heading_raw == ""
    assert "Example Insurance" in chunks[0].body_text
