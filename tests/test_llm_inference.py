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
