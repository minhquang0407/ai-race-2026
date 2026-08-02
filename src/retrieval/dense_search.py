"""Dense/embedding search for ICD retrieval.

Uses SapBERT (biomedical concept bi-encoder) as primary backend.
Falls back to paraphrase-multilingual-MiniLM-L12-v2 (multilingual general), then
to BM25 lexical if neither model is available.

Per pj_document.md (Section II.2), biomedical dense retrieval combined with
English query expansion routes Vietnamese diagnoses through English to the correct
ICD node. LCA graph pruning is the precision filter, not a cross-encoder reranker.

Embeddings are cached to disk after first build:
  data/processed/icd_dense_embeddings.npz

Enable with:
  $env:ENABLE_DENSE_SEARCH=1

Override model:
  $env:DENSE_MODEL_NAME=cambridgeltl/SapBERT-from-PubMedBERT-fulltext
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from .bm25_search import BM25Document, BM25SearchIndex, RetrievalResult

logger = logging.getLogger(__name__)

_PRIMARY_MODEL = "cambridgeltl/SapBERT-from-PubMedBERT-fulltext"
_FALLBACK_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
_DEFAULT_MODEL = os.environ.get("DENSE_MODEL_NAME", _PRIMARY_MODEL)
_EMBEDDING_CACHE = Path(os.environ.get("DENSE_CACHE_PATH", "data/processed/icd_dense_embeddings.npz"))

_ENABLE_DENSE = os.environ.get("ENABLE_DENSE_SEARCH", "").lower() in ("1", "true", "yes")


def _build_doc_text(doc: BM25Document) -> str:
    """Concatenate all searchable terms for a document."""
    return " ".join(filter(None, [doc.text, *doc.aliases]))


class DenseSearchIndex:
    """Semantic search index with biomedical SapBERT backend and layered fallback.

    Priority:
      1. SapBERT (biomedical bi-encoder, ideal for ICD concept matching via English)
      2. paraphrase-multilingual-MiniLM (multilingual general-purpose)
      3. BM25 lexical (always available, no ML dependencies)
    """

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
        """Try models in order: requested -> fallback multilingual -> lexical."""
        for model_id in _resolve_model_chain(self._model_name):
            if self._try_load_model(model_id):
                return
        logger.warning("dense_search: all models failed, falling back to lexical BM25")
        self._fallback = BM25SearchIndex(self.documents)

    def _try_load_model(self, model_id: str) -> bool:
        try:
            import numpy as np
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer(model_id)
            cache = self._cache_path

            if cache.exists():
                cached = np.load(str(cache), allow_pickle=False)
                embeddings = cached["embeddings"]
                if embeddings.shape[0] == len(self.documents):
                    self._embeddings = embeddings
                    self._model = model
                    self._model_name = model_id
                    self._loaded = True
                    logger.info(
                        "dense_search: loaded %d embeddings from cache [%s]",
                        len(self.documents),
                        model_id,
                    )
                    return True
                else:
                    logger.warning(
                        "dense_search: cache shape mismatch (%d vs %d docs), recomputing",
                        embeddings.shape[0],
                        len(self.documents),
                    )

            logger.info("dense_search: encoding %d docs with %s ...", len(self.documents), model_id)
            corpus = [_build_doc_text(doc) for doc in self.documents]
            embeddings = model.encode(
                corpus,
                show_progress_bar=True,
                batch_size=512,
                convert_to_numpy=True,
            )
            cache.parent.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(str(cache), embeddings=embeddings)
            self._embeddings = embeddings
            self._model = model
            self._model_name = model_id
            self._loaded = True
            logger.info("dense_search: embeddings cached to %s", cache)
            return True

        except Exception as exc:
            logger.warning("dense_search: %s failed (%s)", model_id, exc)
            return False

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
        embs = self._embeddings
        norms = np.linalg.norm(embs, axis=1)
        norms = np.where(norms == 0, 1e-9, norms)
        q_norm = float(np.linalg.norm(q_emb))
        if q_norm == 0:
            return []
        sims = (embs @ q_emb) / (norms * q_norm)

        k = min(top_k, len(sims))
        top_indices = np.argpartition(sims, -k)[-k:]
        top_indices = top_indices[np.argsort(-sims[top_indices])]

        results = []
        for idx in top_indices:
            score = float(sims[idx])
            if score <= 0:
                continue
            doc = self.documents[int(idx)]
            results.append(RetrievalResult(doc.id, score, doc.text, source="dense"))
        return results

    @property
    def active_model(self) -> str:
        if self._loaded:
            return self._model_name
        return "bm25-lexical-fallback"


def _resolve_model_chain(requested: str) -> list[str]:
    """Return model load order: requested first, then generic fallback."""
    chain = [requested]
    if requested != _FALLBACK_MODEL:
        chain.append(_FALLBACK_MODEL)
    return chain


__all__ = ["DenseSearchIndex"]
