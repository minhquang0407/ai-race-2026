"""End-to-end extraction pipeline over semantic chunks."""

from __future__ import annotations

import sys

from .chunking import SemanticChunker, TextChunk
from .llm_inference import ChunkExtractor
from .postprocess_llm import deduplicate_entities, postprocess_chunk_record
from .schema import Entity


class ExtractionPipeline:
    """Chunk source text, run extraction, correct spans, and deduplicate."""

    def __init__(
        self,
        chunker: SemanticChunker,
        extractor: ChunkExtractor,
        skip_failed_chunks: bool = True,
    ) -> None:
        self.chunker = chunker
        self.extractor = extractor
        self.skip_failed_chunks = skip_failed_chunks

    def extract(self, source_text: str) -> list[Entity]:
        chunks = self.chunker.split(source_text)
        entities: list[Entity] = []
        for chunk in chunks:
            try:
                record = self.extractor.extract_chunk(chunk)
            except Exception as exc:
                if not self.skip_failed_chunks:
                    raise
                print(
                    f"Skipping failed chunk {chunk.index} [{chunk.start}, {chunk.end}): {exc}",
                    file=sys.stderr,
                )
                continue
            entities.extend(postprocess_chunk_record(record, chunk))
        return deduplicate_entities(entities)

    def split(self, source_text: str) -> list[TextChunk]:
        return self.chunker.split(source_text)


__all__ = ["ExtractionPipeline"]
