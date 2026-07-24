from dataclasses import dataclass

from src.extraction.chunking import SemanticChunker, TextChunk
from src.extraction.pipeline import ExtractionPipeline
from src.extraction.schema import Entity, EntityType, MedicalRecord


@dataclass
class FakeExtractor:
    def extract_chunk(self, chunk: TextChunk) -> MedicalRecord:
        entities = []
        if "ho" in chunk.text:
            entities.append(Entity(text="ho", position=[0, 2], type=EntityType.SYMPTOM))
        if "Aspirin" in chunk.text:
            entities.append(Entity(text="Aspirin", position=[0, 7], type=EntityType.MEDICATION))
        return MedicalRecord(entities=entities)


def test_pipeline_extracts_corrected_global_entities_with_fake_extractor():
    text = "Bệnh nhân ho và dùng Aspirin."
    pipeline = ExtractionPipeline(
        chunker=SemanticChunker(target_size=200, min_size=10, max_size=250),
        extractor=FakeExtractor(),
    )
    entities = pipeline.extract(text)
    by_text = {entity.text: entity for entity in entities}

    assert by_text["ho"].position == [10, 12]
    assert by_text["Aspirin"].position == [21, 28]
    assert by_text["Aspirin"].candidates == []


def test_pipeline_deduplicates_overlap_entities():
    text = "ho ho"
    pipeline = ExtractionPipeline(
        chunker=SemanticChunker(target_size=4, min_size=2, max_size=5, overlap_chars=2),
        extractor=FakeExtractor(),
    )
    entities = pipeline.extract(text)
    assert len({(entity.text, tuple(entity.position), entity.type) for entity in entities}) == len(entities)
