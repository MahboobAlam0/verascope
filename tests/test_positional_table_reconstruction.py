"""
Tests for positional table reconstruction.
"""
from src.ingestion.positional_table_reconstruction import (
    _cluster_rows,
    _split_row_into_cells,
)


def _word(x0, y0, x1, y1, text):
    return (x0, y0, x1, y1, text)


def test_cluster_rows_groups_words_at_same_y_position():
    words = [
        _word(50, 100, 90, 105, "Pre-Existing"),
        _word(300, 100, 340, 105, "Waived"),
        _word(50, 110, 80, 115, "Initial"),
        _word(300, 110, 340, 115, "Waived"),
    ]
    rows = _cluster_rows(words)
    assert len(rows) == 2
    assert {t[2] for t in rows[0]} == {"Pre-Existing", "Waived"}
    assert {t[2] for t in rows[1]} == {"Initial", "Waived"}


def test_cluster_rows_respects_y_tolerance():
    words = [
        _word(50, 100.0, 90, 105, "Label"),
        _word(300, 101.5, 340, 106, "Value"),
    ]
    rows = _cluster_rows(words)
    assert len(rows) == 1


def test_split_row_into_cells_uses_gap_threshold():
    row = [(50.0, 90.0, "Pre-Existing"), (95.0, 120.0, "Disease"), (300.0, 340.0, "Waived")]
    cells = _split_row_into_cells(row)
    assert cells == ["Pre-Existing Disease", "Waived"]


def test_split_row_keeps_close_words_in_same_cell():
    row = [(50.0, 90.0, "Waived"), (92.0, 110.0, "Off")]
    cells = _split_row_into_cells(row)
    assert cells == ["Waived Off"]


def test_regression_label_value_pairing_matches_visual_row_not_reading_order():

    words = [
        _word(50, 486, 90, 491, "Pre-Existing"),
        _word(50, 492, 130, 497, "2yr-exclusions"),
        _word(50, 498, 100, 503, "Initial-Waiting"),
        # Values appear in a DIFFERENT order/position in the word stream:
        _word(349, 498, 364, 503, "WaivedC"),  # belongs to row y=498
        _word(349, 486, 364, 491, "WaivedA"),  # belongs to row y=486
        _word(349, 492, 364, 497, "WaivedB"),  # belongs to row y=492
    ]
    rows = _cluster_rows(words)
    cells_by_row = [_split_row_into_cells(r) for r in rows]
    assert cells_by_row[0] == ["Pre-Existing", "WaivedA"]
    assert cells_by_row[1] == ["2yr-exclusions", "WaivedB"]
    assert cells_by_row[2] == ["Initial-Waiting", "WaivedC"]
