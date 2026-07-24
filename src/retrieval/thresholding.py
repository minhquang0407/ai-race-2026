"""Dynamic thresholding for candidate lists."""

from __future__ import annotations

from .bm25_search import RetrievalResult


def apply_dynamic_threshold(
    results: list[RetrievalResult],
    margin: float = 0.15,
    min_score: float = 0.1,
    max_candidates: int = 3,
) -> list[RetrievalResult]:
    """Keep high-confidence candidates while protecting Jaccard precision."""

    if max_candidates <= 0:
        return []
    filtered = [result for result in results if result.score >= min_score]
    if not filtered:
        return []
    ranked = sorted(filtered, key=lambda result: (-result.score, result.id))
    top_score = ranked[0].score
    kept = [ranked[0]]
    for result in ranked[1:]:
        if len(kept) >= max_candidates:
            break
        if top_score - result.score > margin:
            break
        kept.append(result)
    return kept


__all__ = ["apply_dynamic_threshold"]
