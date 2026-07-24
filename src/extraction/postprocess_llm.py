"""Post-processing utilities for local LLM extraction records."""

from __future__ import annotations

from dataclasses import replace

from .chunking import TextChunk
from .schema import Entity, MedicalRecord
from .validation import local_to_global, validate_span


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
    "find_exact_matches",
    "map_entity_to_global",
    "postprocess_chunk_record",
]
