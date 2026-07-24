"""Lightweight RxNorm dictionary/search index.

RxNorm is not treated as an ICD-style tree in the baseline. We first model it
as a terminology index over concept names and synonyms.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .loaders import normalize_text, read_csv_rows, split_aliases


@dataclass(frozen=True)
class RxNormConcept:
    rxcui: str
    name: str
    tty: str
    synonyms: tuple[str, ...] = ()

    @property
    def search_terms(self) -> tuple[str, ...]:
        return (self.name, *self.synonyms)


class RxNormIndex:
    """Simple lexical RxNorm index with exact and token-overlap search."""

    def __init__(self, concepts: list[RxNormConcept]) -> None:
        self.concepts = concepts
        self.by_rxcui = {concept.rxcui: concept for concept in concepts}
        self._term_to_rxcui: dict[str, set[str]] = {}
        for concept in concepts:
            for term in concept.search_terms:
                self._term_to_rxcui.setdefault(normalize_text(term), set()).add(concept.rxcui)

    @classmethod
    def from_csv(cls, path: str | Path) -> "RxNormIndex":
        concepts: list[RxNormConcept] = []
        for row in read_csv_rows(path):
            concepts.append(
                RxNormConcept(
                    rxcui=row["rxcui"].strip(),
                    name=row["name"].strip(),
                    tty=row.get("tty", "").strip(),
                    synonyms=tuple(split_aliases(row.get("synonyms"))),
                )
            )
        return cls(concepts)

    def exact(self, query: str) -> list[RxNormConcept]:
        rxcuis = self._term_to_rxcui.get(normalize_text(query), set())
        return [self.by_rxcui[rxcui] for rxcui in sorted(rxcuis)]

    def search(self, query: str, top_k: int = 5) -> list[tuple[RxNormConcept, float]]:
        normalized_query = normalize_text(query)
        query_tokens = set(normalized_query.split())
        if not query_tokens:
            return []

        scores: dict[str, float] = {}
        for concept in self.concepts:
            best_score = 0.0
            for term in concept.search_terms:
                normalized_term = normalize_text(term)
                term_tokens = set(normalized_term.split())
                if normalized_query == normalized_term:
                    best_score = max(best_score, 1.0)
                    continue
                if normalized_query in normalized_term or normalized_term in normalized_query:
                    best_score = max(best_score, 0.85)
                overlap = len(query_tokens & term_tokens)
                union = len(query_tokens | term_tokens) or 1
                best_score = max(best_score, overlap / union)
            if best_score > 0:
                scores[concept.rxcui] = best_score

        ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:top_k]
        return [(self.by_rxcui[rxcui], score) for rxcui, score in ranked]


def load_rxnorm_index(path: str | Path = "data/raw/rxnorm_sample.csv") -> RxNormIndex:
    return RxNormIndex.from_csv(path)


__all__ = ["RxNormConcept", "RxNormIndex", "load_rxnorm_index"]
