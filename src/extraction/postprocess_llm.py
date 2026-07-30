"""Post-processing utilities for local LLM extraction records."""

from __future__ import annotations

from dataclasses import replace

from .chunking import TextChunk
from .schema import Entity, EntityType, MedicalRecord
from .validation import local_to_global, validate_span

NOISY_TEXTS = {
    "bé trai",
    "bé gái",
    "trẻ",
    "trẻ sơ sinh",
    "con",
    "bác sĩ",
    "bệnh nhân",
    "người bệnh",
    "bệnh",
    "thuốc",
    "thực phẩm",
    "hóa chất",
    "khám",
    "chẩn đoán",
    "vận động",
    "nhiễm sắc thể x",
    "xq28",
    "gen g6pd",
}
PERSON_ROLE_TEXTS = {
    "bé trai",
    "bé gái",
    "trẻ",
    "trẻ sơ sinh",
    "con",
    "bác sĩ",
    "bệnh nhân",
    "người bệnh",
}
COMMON_DIAGNOSIS_TEXTS = {"bệnh", "chẩn đoán"}
COMMON_SYMPTOM_TEXTS = {
    "hồng cầu",
    "sơ sinh",
    "biến chứng",
    "sàng lọc sớm",
    "sàng lọc sớm các bệnh bẩm sinh",
}
GENE_OR_ENZYME_TEXTS = {"men g6pd", "g6pd", "gen g6pd"}


def find_exact_matches(source_text: str, mention: str) -> list[tuple[int, int]]:
    """Return all half-open exact-match spans for mention in source_text."""

    if not mention:
        return []
    matches: list[tuple[int, int]] = []
    start = 0
    while True:
        index = source_text.find(mention, start)
        if index == -1:
            break
        matches.append((index, index + len(mention)))
        start = index + 1
    return matches


def choose_match(
    matches: list[tuple[int, int]],
    predicted_position: list[int],
    ambiguity_distance: int = 0,
) -> tuple[int, int] | None:
    """Choose the exact match nearest to the LLM-predicted local start."""

    if not matches:
        return None
    if len(matches) == 1:
        return matches[0]

    predicted_start = predicted_position[0]
    ranked = sorted(matches, key=lambda span: abs(span[0] - predicted_start))
    best = ranked[0]
    second = ranked[1]
    best_distance = abs(best[0] - predicted_start)
    second_distance = abs(second[0] - predicted_start)
    if second_distance - best_distance <= ambiguity_distance:
        return None
    return best


def correct_entity_span(entity: Entity, chunk: TextChunk) -> Entity | None:
    """Correct a local entity span inside a chunk or drop unsafe entities."""

    start, end = entity.position
    if validate_span(chunk.text, entity.text, start, end):
        return entity

    matches = find_exact_matches(chunk.text, entity.text)
    chosen = choose_match(matches, entity.position)
    if chosen is None:
        return None
    return entity.model_copy(update={"position": [chosen[0], chosen[1]]})


def map_entity_to_global(entity: Entity, chunk: TextChunk) -> Entity:
    """Map a corrected local entity span to source-level coordinates."""

    global_start, global_end = local_to_global(entity.position[0], entity.position[1], chunk)
    return entity.model_copy(update={"position": [global_start, global_end]})


def postprocess_chunk_record(record: MedicalRecord, chunk: TextChunk) -> list[Entity]:
    """Correct local spans and map all safe entities to global coordinates."""

    output: list[Entity] = []
    for entity in record.entities:
        corrected = correct_entity_span(entity, chunk)
        if corrected is None:
            continue
        output.append(map_entity_to_global(corrected, chunk))
    return output


def normalize_entity_text(text: str) -> str:
    """Normalize entity text for conservative rule-based filters."""

    return " ".join(text.casefold().strip().split())


def is_noisy_entity(entity: Entity) -> bool:
    """Return True for obvious false-positive entities seen in LLM smoke tests."""

    normalized = normalize_entity_text(entity.text)
    entity_type = EntityType(entity.type) if isinstance(entity.type, str) else entity.type
    if normalized in NOISY_TEXTS:
        return True
    if entity_type == EntityType.DIAGNOSIS and normalized in COMMON_DIAGNOSIS_TEXTS:
        return True
    if entity_type == EntityType.SYMPTOM and normalized in PERSON_ROLE_TEXTS:
        return True
    if entity_type == EntityType.SYMPTOM and normalized in COMMON_SYMPTOM_TEXTS:
        return True
    if entity_type == EntityType.SYMPTOM and normalized in GENE_OR_ENZYME_TEXTS:
        return True
    return False


def filter_nested_entities(entities: list[Entity]) -> list[Entity]:
    """Drop shorter same-type entities fully contained in longer spans."""

    keep: list[Entity] = []
    for entity in entities:
        entity_type = str(entity.type)
        entity_start, entity_end = entity.position
        entity_len = entity_end - entity_start
        entity_score = len(entity.assertions) + len(entity.candidates)
        contained_by_richer_longer = False
        for other in entities:
            if other is entity or str(other.type) != entity_type:
                continue
            other_start, other_end = other.position
            other_len = other_end - other_start
            if other_len <= entity_len:
                continue
            if other_start <= entity_start and entity_end <= other_end:
                other_score = len(other.assertions) + len(other.candidates)
                if other_score >= entity_score:
                    contained_by_richer_longer = True
                    break
        if not contained_by_richer_longer:
            keep.append(entity)
    return keep


def filter_noisy_entities(entities: list[Entity]) -> list[Entity]:
    """Apply conservative precision-first filters after span correction."""

    non_noisy = [entity for entity in entities if not is_noisy_entity(entity)]
    return filter_nested_entities(non_noisy)


def deduplicate_entities(entities: list[Entity]) -> list[Entity]:
    """Deduplicate entities produced by overlapping chunks."""

    by_key: dict[tuple[str, str, int, int], Entity] = {}
    order: list[tuple[str, str, int, int]] = []
    for entity in entities:
        key = (str(entity.type), entity.text, entity.position[0], entity.position[1])
        existing = by_key.get(key)
        if existing is None:
            by_key[key] = entity
            order.append(key)
            continue
        entity_score = len(entity.assertions) + len(entity.candidates)
        existing_score = len(existing.assertions) + len(existing.candidates)
        if entity_score > existing_score:
            by_key[key] = entity
    return [by_key[key] for key in order]


__all__ = [
    "choose_match",
    "correct_entity_span",
    "deduplicate_entities",
    "filter_nested_entities",
    "filter_noisy_entities",
    "find_exact_matches",
    "is_noisy_entity",
    "map_entity_to_global",
    "normalize_entity_text",
    "postprocess_chunk_record",
]
