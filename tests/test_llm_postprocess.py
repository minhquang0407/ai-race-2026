import pytest

from src.extraction.chunking import TextChunk
from src.extraction.postprocess_llm import (
    choose_match,
    correct_entity_span,
    deduplicate_entities,
    find_exact_matches,
    postprocess_chunk_record,
)
from src.extraction.schema import AssertionType, Entity, EntityType, MedicalRecord


def test_correct_entity_span_keeps_valid_span():
    chunk = TextChunk("Bệnh nhân ho.", 10, 23, 0)
    entity = Entity(text="ho", position=[10, 12], type=EntityType.SYMPTOM)
    assert correct_entity_span(entity, chunk) == entity


def test_correct_entity_span_fixes_unique_exact_match():
    chunk = TextChunk("Bệnh nhân ho.", 100, 113, 0)
    entity = Entity(text="ho", position=[0, 2], type=EntityType.SYMPTOM)
    corrected = correct_entity_span(entity, chunk)
    assert corrected is not None
    assert corrected.position == [10, 12]


def test_correct_entity_span_drops_missing_text():
    chunk = TextChunk("Bệnh nhân ho.", 0, 13, 0)
    entity = Entity(text="sốt", position=[0, 3], type=EntityType.SYMPTOM)
    assert correct_entity_span(entity, chunk) is None


def test_choose_match_drops_ambiguous_tie():
    matches = [(0, 2), (10, 12)]
    assert choose_match(matches, [5, 7]) is None


def test_postprocess_maps_local_to_global():
    chunk = TextChunk("Bệnh nhân ho.", 100, 113, 0)
    record = MedicalRecord(
        entities=[Entity(text="ho", position=[0, 2], type=EntityType.SYMPTOM)]
    )
    entities = postprocess_chunk_record(record, chunk)
    assert len(entities) == 1
    assert entities[0].position == [110, 112]


def test_deduplicate_keeps_richer_entity():
    plain = Entity(text="ho", position=[0, 2], type=EntityType.SYMPTOM)
    rich = Entity(
        text="ho",
        position=[0, 2],
        type=EntityType.SYMPTOM,
        assertions=[AssertionType.NEGATED],
    )
    assert deduplicate_entities([plain, rich]) == [rich]


def test_find_exact_matches_returns_all_half_open_spans():
    assert find_exact_matches("ho rồi ho", "ho") == [(0, 2), (7, 9)]
