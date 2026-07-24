"""Dense-search interface placeholder.

This deterministic implementation mimics a semantic scorer without loading a
heavy embedding model. It can later be replaced by SapBERT/FAISS behind the same
API.
"""

from __future__ import annotations

from .bm25_search import BM25Document, RetrievalResult


class DenseSearchIndex:
    def __init__(self, documents: list[BM25Document]) -> None:
        self.documents = documents

    def search(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        from .bm25_search import BM25SearchIndex

        # Baseline deterministic dense-like behavior: reuse robust lexical
        # overlap, tagged as dense so ensemble code can distinguish sources.
        sparse = BM25SearchIndex(self.documents)
        return [
            RetrievalResult(result.id, result.score, result.text, source="dense")
            for result in sparse.search(query, top_k=top_k)
        ]


__all__ = ["DenseSearchIndex"]
