from src.extraction.schema import Entity, EntityType
from src.postprocessing import PragmaticGraphPruner, build_icd10_graph


def test_build_icd10_graph_bridge():
    graph = build_icd10_graph()
    assert graph.has_code("E11.9")
    assert graph.lowest_common_ancestor("E11.9", "E11.65") == "E11"


def test_pruner_keeps_same_branch_and_drops_far_branch():
    graph = build_icd10_graph()
    pruner = PragmaticGraphPruner(graph, min_wup=0.5, max_distance=4)

    assert pruner.prune_icd_candidates(["E11.9", "E11.65", "K21.9"]) == ["E11.9", "E11.65"]


def test_pruner_scores_same_branch_above_far_branch():
    graph = build_icd10_graph()
    pruner = PragmaticGraphPruner(graph, min_wup=0.0, max_distance=99)

    scores = pruner.score_icd_candidates([("E11.9", 1.0), ("E11.65", 0.9), ("K21.9", 0.9)])
    by_code = {score.code: score for score in scores}
    assert by_code["E11.65"].ontology_score > by_code["K21.9"].ontology_score
    assert by_code["E11.65"].distance_to_anchor < by_code["K21.9"].distance_to_anchor


def test_pruner_drops_unknown_by_default():
    graph = build_icd10_graph()
    pruner = PragmaticGraphPruner(graph)

    assert pruner.prune_icd_candidates(["E11.9", "BAD"]) == ["E11.9"]


def test_pruner_can_keep_unknown_when_configured():
    graph = build_icd10_graph()
    pruner = PragmaticGraphPruner(graph, keep_unknown=True)

    assert "BAD" in pruner.prune_icd_candidates(["E11.9", "BAD"])


def test_entity_level_pruning_only_for_diagnosis():
    graph = build_icd10_graph()
    pruner = PragmaticGraphPruner(graph)

    diagnosis = Entity(
        text="đái tháo đường tuýp 2",
        position=[0, 21],
        type=EntityType.DIAGNOSIS,
        candidates=["E11.9", "K21.9"],
    )
    pruned = pruner.prune_entity_candidates(diagnosis)
    assert pruned.candidates == ["E11.9"]

    medication = Entity(
        text="Aspirin",
        position=[0, 7],
        type=EntityType.MEDICATION,
        candidates=["243670"],
    )
    assert pruner.prune_entity_candidates(medication) == medication
