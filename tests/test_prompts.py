from src.extraction.prompts import build_extraction_prompt
from src.extraction.schema import AssertionType, EntityType


def test_prompt_contains_schema_constraints():
    prompt = build_extraction_prompt("Bệnh nhân không ho.")

    for entity_type in EntityType:
        assert entity_type.value in prompt
    for assertion in AssertionType:
        assert assertion.value in prompt
    assert "candidates: []" in prompt
    assert "[start, end)" in prompt
    assert "không ho" in prompt
