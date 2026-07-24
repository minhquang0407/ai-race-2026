import pytest

from src.knowledge.icd10_graph import load_icd10_graph
from src.knowledge.rxnorm_index import load_rxnorm_index


def test_icd10_graph_lca_distance_and_similarity():
    graph = load_icd10_graph()

    assert graph.has_code("E11.9")
    assert graph.lowest_common_ancestor("E11.9", "E11.65") == "E11"
    assert graph.distance("E11.9", "E11.65") == 2
    assert graph.wu_palmer_similarity("E11.9", "E11.65") > graph.wu_palmer_similarity("E11.9", "K21.9")
    assert graph.lowest_common_ancestor("E11.9", "K21.9") == "ROOT"


def test_icd10_graph_rejects_unknown_code():
    graph = load_icd10_graph()
    with pytest.raises(KeyError):
        graph.depth("BAD")


def test_rxnorm_index_exact_and_synonym_search():
    index = load_rxnorm_index()

    exact = index.exact("ASA")
    assert [concept.rxcui for concept in exact] == ["1191"]

    results = index.search("aspirin 81 mg po daily", top_k=3)
    assert results[0][0].rxcui == "243670"
    assert results[0][1] >= 0.85


def test_rxnorm_index_paracetamol_alias():
    index = load_rxnorm_index()

    results = index.search("paracetamol", top_k=3)
    assert results[0][0].rxcui == "313782"
