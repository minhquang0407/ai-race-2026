from src.extraction.schema import Entity, EntityType
from src.retrieval import (
    BM25Document,
    BM25SearchIndex,
    CandidateRetriever,
    RetrievalResult,
    apply_dynamic_threshold,
)


def test_bm25_search_finds_icd_diabetes():
    retriever = CandidateRetriever.from_sample_data()
    results = retriever.icd_sparse.search("Type 2 diabetes", top_k=5)
    ids = [result.id for result in results]
    assert "E11" in ids or "E11.9" in ids


def test_rxnorm_retrieval_finds_aspirin_81mg():
    retriever = CandidateRetriever.from_sample_data()
    candidates = retriever.retrieve_rxnorm_candidates("aspirin 81 mg po daily")
    assert candidates[0] == "243670"


def test_dynamic_threshold_keeps_top_one_when_margin_large():
    results = [
        RetrievalResult("A", 0.95),
        RetrievalResult("B", 0.70),
        RetrievalResult("C", 0.69),
    ]
    assert [item.id for item in apply_dynamic_threshold(results, margin=0.15)] == ["A"]


def test_dynamic_threshold_keeps_close_candidates():
    results = [
        RetrievalResult("A", 0.95),
        RetrievalResult("B", 0.90),
        RetrievalResult("C", 0.87),
    ]
    assert [item.id for item in apply_dynamic_threshold(results, margin=0.15, max_candidates=3)] == ["A", "B", "C"]


def test_candidate_retriever_adds_icd_candidates_for_diagnosis():
    retriever = CandidateRetriever.from_sample_data()
    entity = Entity(
        text="Type 2 diabetes mellitus",
        position=[0, 24],
        type=EntityType.DIAGNOSIS,
    )
    output = retriever.retrieve_for_entity(entity)
    assert output.candidates
    assert any(candidate.startswith("E11") for candidate in output.candidates)


def test_candidate_retriever_adds_rxnorm_candidates_for_medication():
    retriever = CandidateRetriever.from_sample_data()
    entity = Entity(text="Aspirin", position=[0, 7], type=EntityType.MEDICATION)
    output = retriever.retrieve_for_entity(entity)
    assert "1191" in output.candidates


def test_candidate_retriever_keeps_symptom_candidates_empty():
    retriever = CandidateRetriever.from_sample_data()
    entity = Entity(text="ho", position=[0, 2], type=EntityType.SYMPTOM)
    output = retriever.retrieve_for_entity(entity)
    assert output.candidates == []


def test_bm25_index_exact_alias_score():
    index = BM25SearchIndex([BM25Document(id="x", text="Aspirin", aliases=("ASA",))])
    assert index.search("ASA")[0].score == 1.0
