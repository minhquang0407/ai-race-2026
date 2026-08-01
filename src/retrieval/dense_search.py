"""Dense/embedding search for ICD retrieval.

Tries to load sentence-transformers for multilingual semantic search.
Falls back to robust lexical overlap (same behavior as before Phase 9) if the
model or dependency is unavailable.

Embeddings are cached to disk so startup after the first run is fast:
  data/processed/icd_dense_embeddings.npz
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from .bm25_search import BM25Document, BM25SearchIndex, RetrievalResult

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
_EMBEDDING_CACHE = Path("data/processed/icd_dense_embeddings.npz")

_ENABLE_DENSE = os.environ.get("ENABLE_DENSE_SEARCH", "").lower() in ("1", "true", "yes")


class DenseSearchIndex:
    """Semantic search index with multilingual embedding backend and lexical fallback."""

    def __init__(
        self,
        documents: list[BM25Document],
        model_name: str = _DEFAULT_MODEL,
        cache_path: Path | None = None,
    ) -> None:
        self.documents = documents
        self._model_name = model_name
        self._cache_path = cache_path or _EMBEDDING_CACHE
        self._embeddings = None
        self._model = None
        self._fallback: BM25SearchIndex | None = None
        self._loaded = False

        if _ENABLE_DENSE:
            self._try_load()
        else:
            self._fallback = BM25SearchIndex(self.documents)

    def _try_load(self) -> None:
        try:
            import numpy as np
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer(self._model_name)

            if self._cache_path.exists():
                cached = np.load(str(self._cache_path), allow_pickle=False)
                embeddings = cached["embeddings"]
                if embeddings.shape[0] == len(self.documents):
                    self._embeddings = embeddings
                    self._model = model
                    self._loaded = True
                    logger.info("dense_search: loaded embeddings from cache (%d docs)", len(self.documents))
                    return

            corpus = [" ".join(doc.aliases) if doc.aliases else doc.text for doc in self.documents]
            logger.info("dense_search: encoding %d documents with %s ...", len(corpus), self._model_name)
            embeddings = model.encode(corpus, show_progress_bar=True, batch_size=512, convert_to_numpy=True)
            self._cache_path.parent.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(str(self._cache_path), embeddings=embeddings)
            self._embeddings = embeddings
            self._model = model
            self._loaded = True
            logger.info("dense_search: embeddings computed and cached")

        except Exception as exc:
            logger.warning("dense_search: falling back to lexical (%s)", exc)
            self._fallback = BM25SearchIndex(self.documents)
            self._loaded = False

    def search(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        if self._loaded and self._model is not None and self._embeddings is not None:
            return self._semantic_search(query, top_k)
        fallback = self._fallback or BM25SearchIndex(self.documents)
        return [
            RetrievalResult(r.id, r.score, r.text, source="dense")
            for r in fallback.search(query, top_k=top_k)
        ]

    def _semantic_search(self, query: str, top_k: int) -> list[RetrievalResult]:
        import numpy as np

        q_emb = self._model.encode([query], convert_to_numpy=True)[0]  # type: ignore[union-attr]
        embs = self._embeddings  # type: ignore[assignment]
        # Cosine similarity: dot product over norms
        norms = np.linalg.norm(embs, axis=1)
        norms = np.where(norms == 0, 1e-9, norms)
        q_norm = np.linalg.norm(q_emb)
        if q_norm == 0:
            return []
        sims = (embs @ q_emb) / (norms * q_norm)

        top_indices = np.argpartition(sims, -min(top_k, len(sims)))[-top_k:]
        top_indices = top_indices[np.argsort(-sims[top_indices])]

        results = []
        for idx in top_indices:
            score = float(sims[idx])
            if score <= 0:
                continue
            doc = self.documents[idx]
            results.append(RetrievalResult(doc.id, score, doc.text, source="dense"))
        return results


__all__ = ["DenseSearchIndex"]
