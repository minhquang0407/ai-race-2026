"""Candidate retrieval for extracted medical entities."""

from __future__ import annotations

from dataclasses import dataclass

from src.extraction.schema import Entity, EntityType
from src.knowledge.icd10_graph import ICD10Graph, load_icd10_graph
from src.knowledge.rxnorm_index import RxNormIndex, load_rxnorm_index
from src.postprocessing.pragmatic_graph import PragmaticGraphPruner

from .bm25_search import BM25Document, BM25SearchIndex, RetrievalResult
from .dense_search import DenseSearchIndex
from .thresholding import apply_dynamic_threshold


@dataclass
class CandidateRetriever:
    icd_sparse: BM25SearchIndex
    rxnorm_index: RxNormIndex
    icd_graph: ICD10Graph
    icd_dense: DenseSearchIndex | None = None
    pruner: PragmaticGraphPruner | None = None
    top_k: int = 5
    margin: float = 0.15
    min_score: float = 0.1
    max_candidates: int = 3

    @classmethod
    def from_sample_data(cls) -> "CandidateRetriever":
        icd_graph = load_icd10_graph()
        rxnorm_index = load_rxnorm_index()
        icd_documents = [
            BM25Document(
                id=code,
                text=f"{code} {icd_graph.name(code)}",
                aliases=(icd_graph.name(code),),
            )
            for code in icd_graph.graph.nodes
            if code != icd_graph.root_code
        ]
        icd_sparse = BM25SearchIndex(icd_documents)
        return cls(
            icd_sparse=icd_sparse,
            icd_dense=DenseSearchIndex(icd_documents),
            rxnorm_index=rxnorm_index,
            icd_graph=icd_graph,
            pruner=PragmaticGraphPruner(icd_graph),
        )

    def retrieve_for_entity(self, entity: Entity) -> Entity:
        entity_type = EntityType(entity.type) if isinstance(entity.type, str) else entity.type
        if entity_type == EntityType.DIAGNOSIS:
            candidates = self.retrieve_icd_candidates(entity.text)
            return entity.model_copy(update={"candidates": candidates})
        if entity_type == EntityType.MEDICATION:
            candidates = self.retrieve_rxnorm_candidates(entity.text)
            return entity.model_copy(update={"candidates": candidates})
        return entity.model_copy(update={"candidates": []})

    def retrieve_for_entities(self, entities: list[Entity]) -> list[Entity]:
        return [self.retrieve_for_entity(entity) for entity in entities]

    def retrieve_icd_candidates(self, query: str) -> list[str]:
        results = self._ensemble_results(
            self.icd_sparse.search(query, top_k=self.top_k),
            self.icd_dense.search(query, top_k=self.top_k) if self.icd_dense else [],
        )
        thresholded = apply_dynamic_threshold(
            results,
            margin=self.margin,
            min_score=self.min_score,
            max_candidates=self.max_candidates,
        )
        candidate_scores = [(result.id, result.score) for result in thresholded]
        if self.pruner is None:
            return [code for code, _ in candidate_scores]
        return self.pruner.prune_icd_candidates(candidate_scores)

    def retrieve_rxnorm_candidates(self, query: str) -> list[str]:
        results = [
            RetrievalResult(concept.rxcui, score, concept.name, source="rxnorm")
            for concept, score in self.rxnorm_index.search(query, top_k=self.top_k)
        ]
        thresholded = apply_dynamic_threshold(
            results,
            margin=self.margin,
            min_score=self.min_score,
            max_candidates=self.max_candidates,
        )
        return [result.id for result in thresholded]

    @staticmethod
    def _ensemble_results(
        sparse_results: list[RetrievalResult],
        dense_results: list[RetrievalResult],
    ) -> list[RetrievalResult]:
        scores: dict[str, RetrievalResult] = {}
        for result in [*sparse_results, *dense_results]:
            existing = scores.get(result.id)
            if existing is None:
                scores[result.id] = result
            else:
                combined_score = max(existing.score, result.score)
                scores[result.id] = RetrievalResult(
                    result.id,
                    combined_score,
                    result.text or existing.text,
                    source="ensemble",
                )
        return sorted(scores.values(), key=lambda item: (-item.score, item.id))


__all__ = ["CandidateRetriever"]
