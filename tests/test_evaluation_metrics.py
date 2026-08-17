from src.evaluation.metrics import evaluate_document, run_evaluation


def test_evaluate_document_all_fields_match():
    actual = {"insurer_and_tpa": {"insurer_name": {"value": "Care Health Insurance Ltd."}}}
    ground_truth = {"insurer_and_tpa.insurer_name.value": "Care Health Insurance Ltd."}
    report = evaluate_document(actual, ground_truth, "test.pdf")
    assert report.accuracy == 1.0
    assert report.matched_fields == 1


def test_evaluate_document_reports_mismatch():
    actual = {"demographics": {"total_lives_covered": {"value": 100}}}
    ground_truth = {"demographics.total_lives_covered.value": 152}
    report = evaluate_document(actual, ground_truth, "test.pdf")
    assert report.accuracy == 0.0
    assert report.field_results[0].match is False
    assert report.field_results[0].expected == 152
    assert report.field_results[0].actual == 100


def test_evaluate_document_missing_field_counts_as_mismatch_not_crash():
    actual = {}  # field entirely absent from actual output
    ground_truth = {"insurer_and_tpa.insurer_name.value": "Some Insurer"}
    report = evaluate_document(actual, ground_truth, "test.pdf")
    assert report.field_results[0].actual is None
    assert report.field_results[0].match is False


def test_evaluate_document_partial_match_computes_correct_accuracy():
    actual = {
        "a": {"value": 1},
        "b": {"value": 999},  # wrong
    }
    ground_truth = {"a.value": 1, "b.value": 2}
    report = evaluate_document(actual, ground_truth, "test.pdf")
    assert report.matched_fields == 1
    assert report.total_fields == 2
    assert report.accuracy == 0.5


def test_run_evaluation_returns_none_when_no_output_files_exist(tmp_path):
    ground_truth_path = tmp_path / "ground_truth.json"
    ground_truth_path.write_text('{"nonexistent.pdf": {"a.value": 1}}')
    empty_output_dir = tmp_path / "output"
    empty_output_dir.mkdir()

    result = run_evaluation(empty_output_dir, ground_truth_path)
    assert result is None  # honest "nothing to evaluate", not a fabricated 0% score


def test_run_evaluation_finds_and_evaluates_existing_output(tmp_path):
    ground_truth_path = tmp_path / "ground_truth.json"
    ground_truth_path.write_text(
        '{"doc.pdf": {"insurer_and_tpa.insurer_name.value": "Test Insurer"}}'
    )
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    (output_dir / "doc.final_output.json").write_text(
        '{"insurer_and_tpa": {"insurer_name": {"value": "Test Insurer"}}}'
    )

    reports = run_evaluation(output_dir, ground_truth_path)
    assert reports is not None
    assert len(reports) == 1
    assert reports[0].accuracy == 1.0
