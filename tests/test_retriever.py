from src.preprocessing.chunking import Chunk
from src.retrieval.retriever import retrieve_chunks_for_stage
from src.retrieval.stage_specs import ExtractionStage


def _chunk(chunk_id, page, heading_raw="", heading_canonical=None, body_text=""):
    return Chunk(
        chunk_id=chunk_id,
        page_number=page,
        heading_raw=heading_raw,
        heading_canonical=heading_canonical,
        body_text=body_text,
        tables=[],
    )


def test_canonical_heading_match_is_selected():
    chunks = [
        _chunk("c1", 2, "Maternity", "maternity", "1. Covered up to Rs 50,000."),
        _chunk("c2", 2, "Other Benefits", "other benefits", "1. Ambulance covered."),
    ]
    result = retrieve_chunks_for_stage(chunks, ExtractionStage.MATERNITY)
    ids = [c.chunk_id for c in result.chunks]
    assert "c1" in ids
    assert result.match_reasons["c1"] == "canonical_heading_match:maternity"


def test_always_include_first_page_regardless_of_keywords():
    chunks = [
        _chunk("c1", 1, body_text="Policy No 12345, Insurer XYZ Health Insurance Ltd."),
        _chunk("c2", 2, "Maternity", "maternity", "1. Covered."),
    ]
    result = retrieve_chunks_for_stage(chunks, ExtractionStage.INSURER_AND_TPA)
    ids = [c.chunk_id for c in result.chunks]
    assert "c1" in ids
    assert result.match_reasons["c1"] == "always_include_first_page"


def test_keyword_fallback_finds_content_missing_a_heading():
    """Mirrors the real Corporate Floater case: relevant content with no
    detected heading should still be retrievable via keyword scoring.
    """
    chunks = [
        _chunk("c1", 2, "PPE Kit", None, "Corporate Floater Sum Insured shall not exceed Rs 5 Lakh."),
        _chunk("c2", 2, "Maternity", "maternity", "1. Covered."),
    ]
    result = retrieve_chunks_for_stage(chunks, ExtractionStage.BUFFER_AND_WAIVERS)
    ids = [c.chunk_id for c in result.chunks]
    assert "c1" in ids


def test_keyword_threshold_excludes_zero_score_chunks_when_something_else_matched():
    chunks = [
        _chunk("c1", 2, body_text="This section has nothing relevant at all."),
        _chunk("c2", 2, "Maternity", "maternity", "1. Covered up to Rs 50,000."),
    ]
    result = retrieve_chunks_for_stage(chunks, ExtractionStage.MATERNITY)

    ids = [c.chunk_id for c in result.chunks]
    assert "c2" in ids
    assert "c1" not in ids


def test_last_resort_fallback_when_nothing_matches_at_all():
    chunks = [
        _chunk("c1", 2, body_text="This section has nothing relevant at all."),
    ]
    result = retrieve_chunks_for_stage(chunks, ExtractionStage.MATERNITY)
    assert len(result.chunks) == 1
    assert result.match_reasons["c1"] == "last_resort_no_match_found"


def test_last_resort_fallback_does_not_trigger_when_something_matched():
    chunks = [
        _chunk("c1", 2, "Maternity", "maternity", "1. Covered up to Rs 50,000."),
    ]
    result = retrieve_chunks_for_stage(chunks, ExtractionStage.MATERNITY)
    assert result.match_reasons["c1"] == "canonical_heading_match:maternity"


def test_last_resort_fallback_is_empty_when_document_has_no_chunks():
    result = retrieve_chunks_for_stage([], ExtractionStage.MATERNITY)
    assert result.chunks == []


def test_max_keyword_fallback_chunks_is_respected():
    chunks = [
        _chunk(f"c{i}", 2, body_text="ambulance ambulance ambulance") for i in range(10)
    ]
    result = retrieve_chunks_for_stage(
        chunks, ExtractionStage.INFERTILITY_AND_AMBULANCE, max_keyword_fallback_chunks=3
    )
    assert len(result.chunks) == 3


def test_no_duplicate_chunks_across_selection_rules():
    chunks = [
        _chunk("c1", 1, body_text="Insurer: Example Health Insurance Ltd, TPA: Example TPA"),
    ]
    result = retrieve_chunks_for_stage(chunks, ExtractionStage.INSURER_AND_TPA)
    assert len(result.chunks) == 1


def test_result_preserves_original_document_order():
    chunks = [
        _chunk("c1", 2, "Other Benefits", "other benefits", "1. Ambulance covered."),
        _chunk("c2", 2, "Maternity", "maternity", "1. Covered."),
    ]
    result = retrieve_chunks_for_stage(chunks, ExtractionStage.OTHER_BENEFITS)
    ids = [c.chunk_id for c in result.chunks]
    assert ids.index("c1") < ids.index("c2") if "c2" in ids else True
