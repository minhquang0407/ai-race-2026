"""Shared data schemas for medical entity extraction.

The competition uses Python-style half-open spans: ``[start, end)``.
That means ``source_text[start:end]`` must exactly equal ``entity.text``.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class EntityType(str, Enum):
    """Allowed entity labels from the competition statement."""

    SYMPTOM = "TRIỆU_CHỨNG"
    TEST_NAME = "TÊN_XÉT_NGHIỆM"
    TEST_RESULT = "KẾT_QUẢ_XÉT_NGHIỆM"
    DIAGNOSIS = "CHẨN_ĐOÁN"
    MEDICATION = "THUỐC"


class AssertionType(str, Enum):
    """Allowed assertion labels for clinical context."""

    NEGATED = "isNegated"
    FAMILY = "isFamily"
    HISTORICAL = "isHistorical"


CANDIDATE_ENTITY_TYPES = {EntityType.DIAGNOSIS, EntityType.MEDICATION}
ASSERTION_ENTITY_TYPES = {
    EntityType.DIAGNOSIS,
    EntityType.MEDICATION,
    EntityType.SYMPTOM,
}


class Entity(BaseModel):
    """A single extracted medical concept in the required JSON format."""

    model_config = ConfigDict(use_enum_values=True)

    text: str = Field(..., min_length=1, description="Exact text span from source input")
    position: list[int] = Field(..., min_length=2, max_length=2, description="Half-open character span [start, end)")
    type: EntityType = Field(..., description="Competition entity type")
    assertions: list[AssertionType] = Field(default_factory=list, max_length=3)
    candidates: list[str] = Field(default_factory=list)

    @field_validator("position")
    @classmethod
    def validate_position(cls, position: list[int]) -> list[int]:
        start, end = position
        if start < 0 or end < 0:
            raise ValueError("position values must be non-negative")
        if start >= end:
            raise ValueError("position must satisfy start < end")
        return position

    @field_validator("assertions")
    @classmethod
    def deduplicate_assertions(cls, assertions: list[AssertionType]) -> list[AssertionType]:
        seen: set[str] = set()
        deduped: list[AssertionType] = []
        for assertion in assertions:
            assertion_value = assertion.value if isinstance(assertion, AssertionType) else str(assertion)
            if assertion_value not in seen:
                seen.add(assertion_value)
                deduped.append(assertion)
        return deduped

    @field_validator("candidates", mode="before")
    @classmethod
    def normalize_candidates(cls, candidates: Any) -> list[str]:
        if candidates is None:
            return []
        return [str(candidate) for candidate in candidates]

    @model_validator(mode="after")
    def validate_type_restricted_fields(self) -> "Entity":
        entity_type = self.type
        if isinstance(entity_type, str):
            entity_type = EntityType(entity_type)

        if self.candidates and entity_type not in CANDIDATE_ENTITY_TYPES:
            raise ValueError("candidates are only allowed for CHẨN_ĐOÁN and THUỐC")
        if self.assertions and entity_type not in ASSERTION_ENTITY_TYPES:
            raise ValueError("assertions are only allowed for CHẨN_ĐOÁN, THUỐC, and TRIỆU_CHỨNG")
        return self


class MedicalRecord(BaseModel):
    """LLM output wrapper used for constrained decoding."""

    entities: list[Entity] = Field(default_factory=list)


__all__ = [
    "AssertionType",
    "CANDIDATE_ENTITY_TYPES",
    "ASSERTION_ENTITY_TYPES",
    "Entity",
    "EntityType",
    "MedicalRecord",
]
