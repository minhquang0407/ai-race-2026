from src.extraction.llm_inference import parse_json_output
from src.extraction.schema import EntityType


def test_parse_json_output_sanitizes_disallowed_assertions_on_fallback():
    record = parse_json_output(
        '''{
          "entities": [
            {"text": "7.2 mmol/L", "position": [0, 9], "type": "KẾT_QUẢ_XÉT_NGHIỆM", "assertions": ["isNegated"], "candidates": []},
            {"text": "ho", "position": [10, 12], "type": "TRIỆU_CHỨNG", "assertions": ["isNegated"], "candidates": []}
          ]
        }'''
    )
    assert len(record.entities) == 2
    assert record.entities[0].type == EntityType.TEST_RESULT
    assert record.entities[0].assertions == []
    assert record.entities[1].assertions == ["isNegated"]


def test_parse_json_output_drops_invalid_entity_on_fallback():
    record = parse_json_output(
        '''{
          "entities": [
            {"text": "bad", "position": [0, 3], "type": "BỆNH", "assertions": [], "candidates": []},
            {"text": "Aspirin", "position": [4, 11], "type": "THUỐC", "assertions": [], "candidates": []}
          ]
        }'''
    )
    assert [entity.text for entity in record.entities] == ["Aspirin"]


def test_parse_json_output_salvages_complete_entities_from_partial_json():
    # Simulates partial JSON: 2 complete entities before truncation
    raw = (
        '{\n  "entities": [\n'
        '    {"text": "ho", "position": [0, 2], "type": "TRIỆU_CHỨNG", "assertions": [], "candidates": []},\n'
        '    {"text": "sốt", "position": [3, 6], "type": "TRIỆU_CHỨNG", "assertions": [], "candidates": []},\n'
        '    {"text": "\u0111'  # truncated mid-string
    )
    record = parse_json_output(raw)
    assert len(record.entities) == 2
    assert record.entities[0].text == "ho"
    assert record.entities[1].text == "sốt"


def test_parse_json_output_salvages_nothing_when_all_objects_partial():
    raw = '{"entities": [{"text": "\u0111'  # only truncated objects
    record = parse_json_output(raw)
    assert record.entities == []


def test_parse_json_output_strict_path_still_works():
    raw = '{"entities": [{"text": "Aspirin", "position": [0, 7], "type": "THUỐC", "assertions": [], "candidates": []}]}'
    record = parse_json_output(raw)
    assert record.entities[0].text == "Aspirin"
