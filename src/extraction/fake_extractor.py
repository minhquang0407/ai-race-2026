"""Rule-based fake extractor for fast integration tests.

This is not the competition solution. It only lets CI exercise the full
pipeline without loading a 7B LLM.
"""

from __future__ import annotations

from .chunking import TextChunk
from .llm_inference import ChunkExtractor
from .schema import AssertionType, Entity, EntityType, MedicalRecord


class FakeExtractor(ChunkExtractor):
    patterns: tuple[tuple[str, EntityType], ...] = (
        ("đái tháo đường tuýp 2", EntityType.DIAGNOSIS),
        ("đái tháo đường", EntityType.DIAGNOSIS),
        ("Type 2 diabetes mellitus", EntityType.DIAGNOSIS),
        ("Aspirin", EntityType.MEDICATION),
        ("aspirin", EntityType.MEDICATION),
        ("ho", EntityType.SYMPTOM),
        ("sốt", EntityType.SYMPTOM),
    )

    def extract_chunk(self, chunk: TextChunk) -> MedicalRecord:
        entities: list[Entity] = []
        occupied: set[tuple[int, int]] = set()
        for pattern, entity_type in self.patterns:
            start = 0
            while True:
                index = chunk.text.find(pattern, start)
                if index == -1:
                    break
                end = index + len(pattern)
                span = (index, end)
                if span not in occupied:
                    occupied.add(span)
                    entities.append(
                        Entity(
                            text=pattern,
                            position=[index, end],
                            type=entity_type,
                            assertions=self._assertions_near(chunk.text, index),
                            candidates=[],
                        )
                    )
                start = index + 1
        return MedicalRecord(entities=entities)

    @staticmethod
    def _assertions_near(text: str, start: int) -> list[AssertionType]:
        window = text[max(0, start - 30) : start].casefold()
        assertions: list[AssertionType] = []
        if any(trigger in window for trigger in ("không", "phủ nhận", "chưa ghi nhận", "âm tính")):
            assertions.append(AssertionType.NEGATED)
        if any(trigger in window for trigger in ("tiền sử", "từng", "đã dùng", "trước nhập viện")):
            assertions.append(AssertionType.HISTORICAL)
        if any(trigger in window for trigger in ("bố", "mẹ", "gia đình", "người thân")):
            assertions.append(AssertionType.FAMILY)
        return assertions


__all__ = ["FakeExtractor"]
