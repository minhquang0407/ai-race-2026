"""Extraction package public API."""

from .chunking import SemanticChunker, TextChunk
from .fake_extractor import FakeExtractor
from .llm_inference import ChunkExtractor, LLMExtractor, parse_json_output
from .pipeline import ExtractionPipeline
from .postprocess_llm import (
    correct_entity_span,
    deduplicate_entities,
    postprocess_chunk_record,
)
from .prompts import build_extraction_prompt
from .schema import AssertionType, Entity, EntityType, MedicalRecord
from .validation import local_to_global, require_valid_span, validate_span

__all__ = [
    "AssertionType",
    "ChunkExtractor",
    "Entity",
    "EntityType",
    "ExtractionPipeline",
    "FakeExtractor",
    "LLMExtractor",
    "MedicalRecord",
    "SemanticChunker",
    "TextChunk",
    "build_extraction_prompt",
    "correct_entity_span",
    "deduplicate_entities",
    "local_to_global",
    "parse_json_output",
    "postprocess_chunk_record",
    "require_valid_span",
    "validate_span",
]

