"""Pragmatic Graph pruning over ICD-10 candidate lists."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from src.extraction.schema import Entity, EntityType
from src.knowledge.icd10_graph import ICD10Graph


@dataclass(frozen=True)
class CandidateScore:
    """Candidate score enriched with ontology information."""

    code: str
    retrieval_score: float = 1.0
    ontology_score: float = 1.0
    final_score: float = 1.0
    distance_to_anchor: int = 0


class PragmaticGraphPruner:
    """Rule-based ICD-10 pruning using LCA and Wu-Palmer similarity."""

    def __init__(
        self,
        icd_graph: ICD10Graph,
        min_wup: float = 0.5,
        max_distance: int = 4,
        alpha: float = 0.7,
        keep_unknown: bool = False,
    ) -> None:
        if not 0 <= min_wup <= 1:
            raise ValueError("min_wup must be between 0 and 1")
        if max_distance < 0:
            raise ValueError("max_distance must be non-negative")
        if not 0 <= alpha <= 1:
            raise ValueError("alpha must be between 0 and 1")
        self.icd_graph = icd_graph
        self.min_wup = min_wup
        self.max_distance = max_distance
        self.alpha = alpha
        self.keep_unknown = keep_unknown

    def prune_icd_candidates(
        self,
        candidates: Iterable[str] | Iterable[tuple[str, float]],
    ) -> list[str]:
        """Return candidate ICD codes after ontology pruning."""

        return [score.code for score in self.score_icd_candidates(candidates)]

    def score_icd_candidates(
        self,
        candidates: Iterable[str] | Iterable[tuple[str, float]],
    ) -> list[CandidateScore]:
        normalized = self._normalize_candidates(candidates)
        if not normalized:
            return []

        known = [(code, score) for code, score in normalized if self.icd_graph.has_code(code)]
        unknown = [(code, score) for code, score in normalized if not self.icd_graph.has_code(code)]
        if not known:
            if not self.keep_unknown:
                return []
            return [CandidateScore(code=code, retrieval_score=score, final_score=score) for code, score in unknown]

        anchor, _ = max(known, key=lambda item: item[1])
        scored: list[CandidateScore] = []
        for code, retrieval_score in known:
            if code == anchor:
                ontology_score = 1.0
                distance = 0
            else:
                ontology_score = self.icd_graph.wu_palmer_similarity(anchor, code)
                distance = self.icd_graph.distance(anchor, code)
                if ontology_score < self.min_wup or distance > self.max_distance:
                    continue
            final_score = self.alpha * retrieval_score + (1 - self.alpha) * ontology_score
            scored.append(
                CandidateScore(
                    code=code,
                    retrieval_score=retrieval_score,
                    ontology_score=ontology_score,
                    final_score=final_score,
                    distance_to_anchor=distance,
                )
            )

        if self.keep_unknown:
            scored.extend(
                CandidateScore(code=code, retrieval_score=score, ontology_score=0.0, final_score=self.alpha * score)
                for code, score in unknown
            )

        return sorted(scored, key=lambda item: (-item.final_score, item.code))

    def prune_entity_candidates(self, entity: Entity) -> Entity:
        """Prune candidates for diagnosis entities; leave other entities untouched."""

        entity_type = EntityType(entity.type) if isinstance(entity.type, str) else entity.type
        if entity_type != EntityType.DIAGNOSIS or not entity.candidates:
            return entity
        pruned = self.prune_icd_candidates(entity.candidates)
        return entity.model_copy(update={"candidates": pruned})

    @staticmethod
    def _normalize_candidates(
        candidates: Iterable[str] | Iterable[tuple[str, float]],
    ) -> list[tuple[str, float]]:
        normalized: list[tuple[str, float]] = []
        seen: set[str] = set()
        for item in candidates:
            if isinstance(item, tuple):
                code, score = item
            else:
                code, score = item, 1.0
            code = str(code).strip()
            if not code or code in seen:
                continue
            seen.add(code)
            normalized.append((code, float(score)))
        return normalized


__all__ = ["CandidateScore", "PragmaticGraphPruner"]
