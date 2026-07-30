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


def test_filter_noisy_entities_drops_known_false_positives():
    from src.extraction.postprocess_llm import filter_noisy_entities

    entities = [
        Entity(text="bé trai", position=[0, 7], type=EntityType.SYMPTOM),
        Entity(text="bác sĩ", position=[8, 14], type=EntityType.SYMPTOM),
        Entity(text="thuốc", position=[15, 20], type=EntityType.MEDICATION),
        Entity(text="bệnh", position=[21, 25], type=EntityType.DIAGNOSIS),
        Entity(text="khó thở", position=[26, 33], type=EntityType.SYMPTOM),
        Entity(text="Aspirin", position=[34, 41], type=EntityType.MEDICATION),
        Entity(text="thiếu men G6PD", position=[42, 56], type=EntityType.DIAGNOSIS),
    ]

    kept = filter_noisy_entities(entities)
    assert [entity.text for entity in kept] == ["khó thở", "Aspirin", "thiếu men G6PD"]


def test_filter_noisy_entities_drops_nested_same_type_entity():
    from src.extraction.postprocess_llm import filter_noisy_entities

    entities = [
        Entity(text="chậm phát triển trí tuệ", position=[0, 23], type=EntityType.SYMPTOM),
        Entity(text="triển trí tuệ", position=[10, 23], type=EntityType.SYMPTOM),
        Entity(text="vàng da", position=[30, 37], type=EntityType.SYMPTOM),
    ]

    assert [entity.text for entity in filter_noisy_entities(entities)] == [
        "chậm phát triển trí tuệ",
        "vàng da",
    ]


def test_filter_noisy_entities_drops_symptom_structural_noise():
    from src.extraction.postprocess_llm import filter_noisy_entities

    entities = [
        # structural SYMPTOM noise -> dropped by filter
        Entity(text="men G6PD", position=[20, 28], type=EntityType.SYMPTOM),
        Entity(text="hồng cầu", position=[30, 38], type=EntityType.SYMPTOM),
        Entity(text="sàng lọc sớm các bệnh bẩm sinh", position=[40, 70], type=EntityType.SYMPTOM),
        Entity(text="sơ sinh", position=[71, 78], type=EntityType.SYMPTOM),
        Entity(text="biến chứng", position=[79, 89], type=EntityType.SYMPTOM),
        # MEDICATION entities pass filter (handled by RxNorm gate in retriever)
        Entity(text="men G6PD", position=[0, 8], type=EntityType.MEDICATION),
        Entity(text="long não", position=[90, 98], type=EntityType.MEDICATION),
        Entity(text="Aspirin", position=[200, 207], type=EntityType.MEDICATION),
        # valid entities -> kept
        Entity(text="thiếu men G6PD", position=[10, 24], type=EntityType.DIAGNOSIS),
        Entity(text="khó thở", position=[140, 147], type=EntityType.SYMPTOM),
    ]

    kept = [entity.text for entity in filter_noisy_entities(entities)]
    # diagnosis and symptom valid -> kept
    assert "thiếu men G6PD" in kept
    assert "khó thở" in kept
    # structural symptom noise -> dropped
    assert "hồng cầu" not in kept
    assert "sơ sinh" not in kept
    assert "biến chứng" not in kept
    # gene/enzyme as symptom -> dropped
    assert all(e.type != EntityType.SYMPTOM or e.text != "men G6PD" for e in filter_noisy_entities(entities))
    # medication entities pass filter layer (gate is in retriever, not here)
    assert "Aspirin" in kept
