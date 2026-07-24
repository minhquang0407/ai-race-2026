import json

from main import main


def test_main_pipeline_writes_submission_json(tmp_path):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    (input_dir / "1.txt").write_text(
        "Bệnh nhân có tiền sử đái tháo đường tuýp 2, hiện không ho và dùng Aspirin.",
        encoding="utf-8",
    )

    exit_code = main([
        "--input-dir",
        str(input_dir),
        "--output-dir",
        str(output_dir),
        "--extractor",
        "fake",
    ])

    assert exit_code == 0
    output_path = output_dir / "1.json"
    assert output_path.exists()
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert isinstance(payload, list)
    by_text = {item["text"]: item for item in payload}
    assert "Aspirin" in by_text
    assert by_text["Aspirin"]["candidates"]
    assert any("đái tháo đường" in item["text"] for item in payload)


def test_main_pipeline_natural_sort_and_limit(tmp_path):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    (input_dir / "10.txt").write_text("Aspirin", encoding="utf-8")
    (input_dir / "2.txt").write_text("Aspirin", encoding="utf-8")

    assert main(["--input-dir", str(input_dir), "--output-dir", str(output_dir), "--limit", "1"]) == 0
    assert (output_dir / "2.json").exists()
    assert not (output_dir / "10.json").exists()
