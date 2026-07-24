"""Sparse lexical/BM25-style search utilities."""

from __future__ import annotations

from dataclasses import dataclass

from src.knowledge.loaders import normalize_text


@dataclass(frozen=True)
class BM25Document:
    id: str
    text: str
    aliases: tuple[str, ...] = ()

    @property
    def terms(self) -> tuple[str, ...]:
        return (self.text, *self.aliases)


@dataclass(frozen=True)
class RetrievalResult:
    id: str
    score: float
    text: str = ""
    source: str = "sparse"


class BM25SearchIndex:
    """A small lexical index with optional rank_bm25 backend and safe fallback."""

    def __init__(self, documents: list[BM25Document]) -> None:
        self.documents = documents
        self._use_rank_bm25 = False
        self._bm25 = None
        self._corpus_tokens: list[list[str]] = []
        for document in documents:
            searchable = " ".join(document.terms)
            self._corpus_tokens.append(self._tokenize(searchable))
        try:
            from rank_bm25 import BM25Okapi

            self._bm25 = BM25Okapi(self._corpus_tokens)
            self._use_rank_bm25 = True
        except Exception:
            self._bm25 = None
            self._use_rank_bm25 = False

    def search(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        if self._use_rank_bm25 and self._bm25 is not None:
            raw_scores = self._bm25.get_scores(query_tokens)
            max_score = max(raw_scores) if len(raw_scores) else 0
            scored = []
            for document, raw_score in zip(self.documents, raw_scores):
                score = float(raw_score / max_score) if max_score > 0 else 0.0
                score = max(score, self._fallback_score(query, document))
                if score > 0:
                    scored.append(RetrievalResult(document.id, score, document.text))
        else:
            scored = [
                RetrievalResult(document.id, self._fallback_score(query, document), document.text)
                for document in self.documents
            ]
            scored = [result for result in scored if result.score > 0]

        return sorted(scored, key=lambda result: (-result.score, result.id))[:top_k]

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return normalize_text(text).replace("/", " ").replace("-", " ").split()

    @classmethod
    def _fallback_score(cls, query: str, document: BM25Document) -> float:
        normalized_query = normalize_text(query)
        query_tokens = set(cls._tokenize(query))
        if not query_tokens:
            return 0.0
        best = 0.0
        for term in document.terms:
            normalized_term = normalize_text(term)
            term_tokens = set(cls._tokenize(term))
            if normalized_query == normalized_term:
                best = max(best, 1.0)
            elif normalized_query in normalized_term or normalized_term in normalized_query:
                best = max(best, 0.85)
            union = len(query_tokens | term_tokens) or 1
            best = max(best, len(query_tokens & term_tokens) / union)
        return best


__all__ = ["BM25Document", "BM25SearchIndex", "RetrievalResult"]
