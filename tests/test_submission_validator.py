import json

from src.evaluation.submission_validator import validate_submission_batch, validate_submission_file


def write_pair(tmp_path, text, payload, name="1"):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)
    input_path = input_dir / f"{name}.txt"
    output_path = output_dir / f"{name}.json"
    input_path.write_text(text, encoding="utf-8")
    output_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return input_path, output_path, input_dir, output_dir


def issue_codes(report):
    return {issue.code for issue in report.issues}


def test_valid_submission_file():
    # positions: Bệnh nhân ho dùng Aspirin
    text = "Bệnh nhân ho dùng Aspirin"
    payload = [
        {"text": "ho", "position": [10, 12], "type": "TRIỆU_CHỨNG", "assertions": [], "candidates": []},
        {"text": "Aspirin", "position": [18, 25], "type": "THUỐC", "assertions": [], "candidates": ["1191"]},
    ]
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as d:
        input_path, output_path, *_ = write_pair(Path(d), text, payload)
        report = validate_submission_file(input_path, output_path)
    assert report.is_valid
    assert report.valid_files == 1


def test_missing_output_file(tmp_path):
    input_path = tmp_path / "1.txt"
    input_path.write_text("abc", encoding="utf-8")
    report = validate_submission_file(input_path, tmp_path / "1.json")
    assert "missing_output" in issue_codes(report)


def test_invalid_json_and_root_not_array(tmp_path):
    input_path = tmp_path / "1.txt"
    output_path = tmp_path / "1.json"
    input_path.write_text("abc", encoding="utf-8")
    output_path.write_text("{bad", encoding="utf-8")
    assert "invalid_json" in issue_codes(validate_submission_file(input_path, output_path))

    output_path.write_text('{"entities": []}', encoding="utf-8")
    assert "root_not_array" in issue_codes(validate_submission_file(input_path, output_path))


def test_missing_field_invalid_type_assertion_and_candidate_rule(tmp_path):
    text = "Bệnh nhân ho"
    payload = [
        {"text": "ho", "position": [10, 12], "type": "BỆNH", "assertions": ["bad"], "candidates": ["X"]},
        {"text": "ho", "position": [10, 12], "type": "TRIỆU_CHỨNG", "assertions": [], "extra": 1},
        {"text": "ho", "position": [10, 12], "type": "TRIỆU_CHỨNG", "assertions": [], "candidates": ["X"]},
    ]
    input_path, output_path, *_ = write_pair(tmp_path, text, payload)
    codes = issue_codes(validate_submission_file(input_path, output_path))
    assert "invalid_type" in codes
    assert "invalid_assertion" in codes
    assert "candidates_not_allowed" in codes
    assert "missing_keys" in codes
    assert "extra_keys" in codes


def test_invalid_span_and_text_mismatch(tmp_path):
    text = "Bệnh nhân ho"
    payload = [
        {"text": "ho", "position": [99, 100], "type": "TRIỆU_CHỨNG", "assertions": [], "candidates": []},
        {"text": "sốt", "position": [10, 12], "type": "TRIỆU_CHỨNG", "assertions": [], "candidates": []},
    ]
    input_path, output_path, *_ = write_pair(tmp_path, text, payload)
    codes = issue_codes(validate_submission_file(input_path, output_path))
    assert "position_out_of_bounds" in codes
    assert "span_text_mismatch" in codes


def test_batch_report(tmp_path):
    payload = [{"text": "ho", "position": [10, 12], "type": "TRIỆU_CHỨNG", "assertions": [], "candidates": []}]
    _, _, input_dir, output_dir = write_pair(tmp_path, "Bệnh nhân ho", payload, name="1")
    (input_dir / "2.txt").write_text("missing output", encoding="utf-8")
    report = validate_submission_batch(input_dir, output_dir)
    assert report.checked_files == 2
    assert report.valid_files == 1
    assert "missing_output" in issue_codes(report)
