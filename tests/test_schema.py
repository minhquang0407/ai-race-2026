import pytest
from pydantic import ValidationError

from src.extraction.schema import AssertionType, Entity, EntityType, MedicalRecord


def test_accepts_all_competition_entity_types():
    for entity_type in EntityType:
        entity = Entity(text="abc", position=[0, 3], type=entity_type)
        assert entity.type == entity_type.value


def test_accepts_all_assertion_types_for_supported_entities():
    entity = Entity(
        text="ho",
        position=[0, 2],
        type=EntityType.SYMPTOM,
        assertions=list(AssertionType),
    )
    assert entity.assertions == [item.value for item in AssertionType]


def test_rejects_unknown_type_and_assertion():
    with pytest.raises(ValidationError):
        Entity(text="abc", position=[0, 3], type="BỆNH")

    with pytest.raises(ValidationError):
        Entity(text="abc", position=[0, 3], type=EntityType.SYMPTOM, assertions=["bad"])


def test_rejects_invalid_positions():
    for position in ([0], [0, 1, 2], [-1, 2], [2, 2], [3, 2]):
        with pytest.raises(ValidationError):
            Entity(text="abc", position=position, type=EntityType.SYMPTOM)


def test_candidates_only_for_diagnosis_and_medication():
    assert Entity(text="aspirin", position=[0, 7], type=EntityType.MEDICATION, candidates=[123]).candidates == ["123"]
    assert Entity(text="gerd", position=[0, 4], type=EntityType.DIAGNOSIS, candidates=["K21.9"]).candidates == ["K21.9"]

    with pytest.raises(ValidationError):
        Entity(text="ho", position=[0, 2], type=EntityType.SYMPTOM, candidates=["R05"])


def test_assertions_only_for_diagnosis_medication_symptom():
    with pytest.raises(ValidationError):
        Entity(
            text="WBC",
            position=[0, 3],
            type=EntityType.TEST_NAME,
            assertions=[AssertionType.HISTORICAL],
        )


def test_medical_record_json_schema_is_available():
    schema = MedicalRecord.model_json_schema()
    assert "entities" in schema["properties"]
