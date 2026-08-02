"""Candidate retrieval for extracted medical entities."""

from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata

from src.extraction.schema import Entity, EntityType
from src.knowledge.icd10_graph import ICD10Graph, load_icd10_graph
from src.knowledge.rxnorm_index import RxNormIndex, load_rxnorm_index
from src.postprocessing.pragmatic_graph import PragmaticGraphPruner

from .bm25_search import BM25Document, BM25SearchIndex, RetrievalResult
from .dense_search import DenseSearchIndex
from .query_expansion import CachingQueryExpander, QueryExpansion
from .thresholding import apply_dynamic_threshold

ICD_GENERIC_TOKENS = {
    "bao",
    "benh",
    "cap",
    "chung",
    "da",
    "dai",
    "day",
    "gan",
    "hoi",
    "man",
    "mo",
    "ruot",
    "te",
    "tu",
    "ung",
    "viem",
}
ICD_SITE_TOKENS = {
    "bao",
    "buong",
    "dai",
    "duong",
    "gan",
    "giap",
    "kich",
    "mat",
    "nghien",
    "ruot",
    "ruou",
    "thich",
    "trung",
    "tuyen",
}


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
    # Ontology gates: drop entities whose best candidate score is below this threshold.
    # Set to 0.0 to disable the gate for that type.
    rxnorm_gate_min_score: float = 0.3
    icd_gate_min_score: float = 0.0
    expander: CachingQueryExpander | None = None

    @classmethod
    def from_sample_data(cls) -> "CandidateRetriever":
        return cls.from_data(
            icd_path="data/raw/icd10_sample.csv",
            rxnorm_path="data/raw/rxnorm_sample.csv",
        )

    @classmethod
    def from_data(
        cls,
        icd_path: str = "data/raw/icd10_sample.csv",
        rxnorm_path: str = "data/raw/rxnorm_sample.csv",
        expander: CachingQueryExpander | None = None,
    ) -> "CandidateRetriever":
        icd_graph = load_icd10_graph(icd_path)
        rxnorm_index = load_rxnorm_index(rxnorm_path)
        icd_documents = [
            BM25Document(
                id=code,
                text=" ".join([code, name, *aliases]),
                aliases=(name, *aliases),
            )
            for code, name, aliases in icd_graph.iter_search_documents()
            if not code.startswith(("CHAPTER_", "SECTION_"))
        ]
        icd_sparse = BM25SearchIndex(icd_documents)
        return cls(
            icd_sparse=icd_sparse,
            icd_dense=DenseSearchIndex(icd_documents),
            rxnorm_index=rxnorm_index,
            icd_graph=icd_graph,
            pruner=PragmaticGraphPruner(icd_graph),
            expander=expander or CachingQueryExpander(),
        )

    def retrieve_for_entity(self, entity: Entity) -> Entity | None:
        """Return the entity with candidates filled in, or None if it fails the ontology gate."""

        entity_type = EntityType(entity.type) if isinstance(entity.type, str) else entity.type
        if entity_type == EntityType.DIAGNOSIS:
            candidates, best_score = self._retrieve_icd_with_score(entity.text)
            if self.icd_gate_min_score > 0.0 and best_score < self.icd_gate_min_score:
                return None
            return entity.model_copy(update={"candidates": candidates})
        if entity_type == EntityType.MEDICATION:
            candidates, best_score = self._retrieve_rxnorm_with_score(entity.text)
            if self.rxnorm_gate_min_score > 0.0 and best_score < self.rxnorm_gate_min_score:
                return None
            return entity.model_copy(update={"candidates": candidates})
        return entity.model_copy(update={"candidates": []})

    def retrieve_for_entities(self, entities: list[Entity]) -> list[Entity]:
        output: list[Entity] = []
        for entity in entities:
            result = self.retrieve_for_entity(entity)
            if result is not None:
                output.append(result)
        return output

    def retrieve_icd_candidates(self, query: str) -> list[str]:
        candidates, _ = self._retrieve_icd_with_score(query)
        return candidates

    def _retrieve_icd_with_score(self, query: str) -> tuple[list[str], float]:
        """Return (candidates, best_score). best_score is 0.0 if nothing matches."""

        expansion = self.expander.expand(query) if self.expander else QueryExpansion(original=query)
        weighted_queries = expansion.all_queries()

        # Collect scored results across all query variants.
        merged: dict[str, RetrievalResult] = {}
        for q_text, q_weight in weighted_queries:
            raw = self._ensemble_results(
                self.icd_sparse.search(q_text, top_k=self.top_k),
                self.icd_dense.search(q_text, top_k=self.top_k) if self.icd_dense else [],
            )
            for result in raw:
                existing = merged.get(result.id)
                new_score = result.score * q_weight
                if existing is None or new_score > existing.score:
                    merged[result.id] = RetrievalResult(result.id, new_score, result.text, source=result.source)
        results = sorted(merged.values(), key=lambda r: (-r.score, r.id))

        # Apply guardrails on the merged pool.
        # Skip the Vietnamese-token guard when expansion fired with high confidence:
        # the English queries already anchor retrieval; applying Vi-token guard over
        # English ICD names would incorrectly drop valid matches (e.g. bàn chân bẹt
        # → "pes planus" → M21.4 "Flat foot [pes planus]").
        if expansion.confidence != "high":
            results = self._guard_icd_results(query, results)
        if expansion.must_have_terms:
            results = self._apply_must_have_guard(expansion.must_have_terms, results)

        thresholded = apply_dynamic_threshold(
            results,
            margin=self.margin,
            min_score=self.min_score,
            max_candidates=self.max_candidates,
        )
        if not thresholded:
            return [], 0.0
        candidate_scores = [(result.id, result.score) for result in thresholded]
        best_score = thresholded[0].score
        if self.pruner is None:
            return [code for code, _ in candidate_scores], best_score
        return self.pruner.prune_icd_candidates(candidate_scores), best_score

    def retrieve_rxnorm_candidates(self, query: str) -> list[str]:
        candidates, _ = self._retrieve_rxnorm_with_score(query)
        return candidates

    def _retrieve_rxnorm_with_score(self, query: str) -> tuple[list[str], float]:
        """Return (candidates, best_score). best_score is 0.0 if nothing matches."""

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
        if not thresholded:
            return [], 0.0
        return [result.id for result in thresholded], thresholded[0].score

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

    @classmethod
    def _apply_must_have_guard(
        cls, must_have_terms: list[str], results: list[RetrievalResult]
    ) -> list[RetrievalResult]:
        """Drop candidates that don't contain any must-have anchor term.

        If ALL candidates are filtered out (none contain any anchor),
        return empty list — prefer no candidates over wrong candidates.
        This prevents generic BM25 token overlaps from sneaking through.
        """
        if not must_have_terms:
            return results
        anchors = {cls._strip_diacritics(t).lower() for t in must_have_terms}
        kept = [
            result for result in results
            if any(anchor in cls._strip_diacritics(result.text) for anchor in anchors)
        ]
        return kept  # intentionally return [] if nothing passes the anchor gate

    @classmethod
    def _guard_icd_results(cls, query: str, results: list[RetrievalResult]) -> list[RetrievalResult]:
        query_tokens = cls._meaningful_icd_tokens(query)
        if not query_tokens:
            return results
        guarded: list[RetrievalResult] = []
        for result in results:
            candidate_tokens = cls._meaningful_icd_tokens(result.text)
            if query_tokens & candidate_tokens:
                guarded.append(result)
        return guarded

    @staticmethod
    def _strip_diacritics(text: str) -> str:
        decomposed = unicodedata.normalize("NFD", text.casefold())
        return "".join(char for char in decomposed if unicodedata.category(char) != "Mn").replace("đ", "d")

    @classmethod
    def _meaningful_icd_tokens(cls, text: str) -> set[str]:
        normalized = cls._strip_diacritics(text)
        tokens = set(re.findall(r"[a-z0-9]+", normalized))
        non_generic = {token for token in tokens if token not in ICD_GENERIC_TOKENS and len(token) > 1}
        site_tokens = tokens & ICD_SITE_TOKENS
        return non_generic | site_tokens


__all__ = ["CandidateRetriever"]
