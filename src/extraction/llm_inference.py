"""LLM inference wrapper for chunk-level extraction."""

from __future__ import annotations

import json
from typing import Protocol

from pydantic import ValidationError

from .chunking import TextChunk
from .prompts import build_extraction_prompt
from .schema import MedicalRecord


class ChunkExtractor(Protocol):
    """Protocol used by the extraction pipeline and fake test extractors."""

    def extract_chunk(self, chunk: TextChunk) -> MedicalRecord:
        """Extract a MedicalRecord from one chunk."""


def parse_json_output(output_text: str) -> MedicalRecord:
    """Parse a model JSON string into a MedicalRecord.

    Some models may emit whitespace around JSON. The constrained decoder should
    prevent prose, but this parser still extracts the outermost JSON object as a
    safety net.
    """

    text = output_text.strip()
    if not text:
        return MedicalRecord(entities=[])

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("model output does not contain a JSON object")
    payload = json.loads(text[start : end + 1])
    try:
        return MedicalRecord.model_validate(payload)
    except ValidationError:
        raise


class LLMExtractor:
    """Qwen/lm-format-enforcer extractor loaded lazily to keep tests lightweight."""

    def __init__(
        self,
        model_id: str = "Qwen/Qwen2.5-7B-Instruct",
        max_new_tokens: int = 512,
        load_in_4bit: bool = True,
    ) -> None:
        self.model_id = model_id
        self.max_new_tokens = max_new_tokens
        self.load_in_4bit = load_in_4bit
        self._tokenizer = None
        self._model = None
        self._prefix_function = None

    def load(self) -> None:
        """Load tokenizer/model and constrained decoding objects."""

        if self._model is not None:
            return

        import torch
        import transformers
        from lmformatenforcer import JsonSchemaParser
        from lmformatenforcer.integrations.transformers import (
            build_transformers_prefix_allowed_tokens_fn,
        )
        from transformers import AutoModelForCausalLM, AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(self.model_id)
        quantization_config = None
        if self.load_in_4bit:
            quantization_config = transformers.BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
            )
        model = AutoModelForCausalLM.from_pretrained(
            self.model_id,
            device_map="auto",
            quantization_config=quantization_config,
        )
        parser = JsonSchemaParser(MedicalRecord.model_json_schema())
        self._tokenizer = tokenizer
        self._model = model
        self._prefix_function = build_transformers_prefix_allowed_tokens_fn(tokenizer, parser)

    def extract_chunk(self, chunk: TextChunk) -> MedicalRecord:
        self.load()
        assert self._tokenizer is not None
        assert self._model is not None
        assert self._prefix_function is not None

        import torch

        prompt = build_extraction_prompt(chunk.text)
        inputs = self._tokenizer(prompt, return_tensors="pt").to(self._model.device)
        with torch.no_grad():
            output_ids = self._model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                prefix_allowed_tokens_fn=self._prefix_function,
                pad_token_id=self._tokenizer.eos_token_id,
            )
        generated_text = self._tokenizer.decode(
            output_ids[0][inputs.input_ids.shape[-1] :],
            skip_special_tokens=True,
        )
        return parse_json_output(generated_text)

    def extract_chunks(self, chunks: list[TextChunk]) -> list[MedicalRecord]:
        return [self.extract_chunk(chunk) for chunk in chunks]


__all__ = ["ChunkExtractor", "LLMExtractor", "parse_json_output"]
