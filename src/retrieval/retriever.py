"""
Chunk retrieval for a given extraction stage (Phase 6).

See src/retrieval/stage_specs.py for the design rationale behind the hybrid
strategy (canonical heading match + keyword-overlap fallback + always-include
first page for metadata stages).
"""
from __future__ import annotations

from pydantic import BaseModel

from src.preprocessing.chunking import Chunk
from src.retrieval.stage_specs import STAGE_SPECS, ExtractionStage, StageRetrievalSpec


class RetrievalResult(BaseModel):
    stage: ExtractionStage
    chunks: list[Chunk]
    match_reasons: dict[str, str] = {}  # chunk_id -> why it was retrieved, for debugging/eval


def _keyword_score(text_lower: str, keywords: list[str]) -> int:
    return sum(1 for kw in keywords if kw in text_lower)


def retrieve_chunks_for_stage(
    chunks: list[Chunk],
    stage: ExtractionStage,
    keyword_score_threshold: int = 1,
    max_keyword_fallback_chunks: int = 3,
) -> RetrievalResult:
    """Select the chunks relevant to a given extraction stage.

    Selection order (a chunk may be included by more than one rule, but is
    only added once):
      1. Any chunk whose heading_canonical matches one of the stage's
         canonical_headings.
      2. If the stage is flagged always_include_first_page, all chunks on
         page 1.
      3. Up to `max_keyword_fallback_chunks` additional chunks (not already
         selected) ranked by keyword-overlap score, provided their score
         meets `keyword_score_threshold`.
      4. Last resort: if rules 1-3 found NOTHING, fall back to every chunk
         in the document rather than sending the LLM nothing. This was
         expected to be purely defensive (for a future insurer with
         unfamiliar terminology), but checking it against the real sample
         set found it ALSO fires today, on a real GMC document:
         `1_Policy_Copy.pdf`'s `buffer_and_waivers` stage previously
         retrieved zero chunks and silently defaulted to not_specified
         without the LLM ever being asked. It now gets the whole (short,
         4-page) document instead - a real gap this closes, not just a
         hypothetical one. (The GPA/Liberty non-GMC documents also trigger
         it in isolated retrieval testing, but never in the real pipeline,
         since Stage 0 classification short-circuits them before retrieval
         ever runs.) This costs more tokens on whatever document/stage
         combination hits it - a deliberate tradeoff against guaranteed
         information loss, and bounded to only the rare case where nothing
         else matched at all.
    """
    spec: StageRetrievalSpec = STAGE_SPECS[stage]
    selected: dict[str, Chunk] = {}
    match_reasons: dict[str, str] = {}

    # Rule 1: canonical heading match.
    if spec.canonical_headings:
        for chunk in chunks:
            if chunk.heading_canonical in spec.canonical_headings:
                selected[chunk.chunk_id] = chunk
                match_reasons[chunk.chunk_id] = (
                    f"canonical_heading_match:{chunk.heading_canonical}"
                )

    # Rule 2: always include page 1 for metadata-type stages.
    if spec.always_include_first_page:
        for chunk in chunks:
            if chunk.page_number == 1 and chunk.chunk_id not in selected:
                selected[chunk.chunk_id] = chunk
                match_reasons[chunk.chunk_id] = "always_include_first_page"

    # Rule 3: keyword-overlap fallback for remaining chunks.
    if spec.keywords:
        scored: list[tuple[int, Chunk]] = []
        for chunk in chunks:
            if chunk.chunk_id in selected:
                continue
            text_lower = chunk.to_context_string().lower()
            score = _keyword_score(text_lower, spec.keywords)
            if score >= keyword_score_threshold:
                scored.append((score, chunk))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        for score, chunk in scored[:max_keyword_fallback_chunks]:
            selected[chunk.chunk_id] = chunk
            match_reasons[chunk.chunk_id] = f"keyword_score:{score}"

    # Rule 4: last resort - nothing matched via heading/first-page/keywords.
    if not selected and chunks:
        for chunk in chunks:
            selected[chunk.chunk_id] = chunk
            match_reasons[chunk.chunk_id] = "last_resort_no_match_found"

    # Preserve original document order in the returned chunk list.
    ordered = [c for c in chunks if c.chunk_id in selected]

    return RetrievalResult(stage=stage, chunks=ordered, match_reasons=match_reasons)
