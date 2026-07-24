"""Internal scoring helpers inspired by the competition metrics."""

from __future__ import annotations


def word_error_rate(reference: str, hypothesis: str) -> float:
    ref_words = reference.split()
    hyp_words = hypothesis.split()
    if not ref_words:
        return 0.0 if not hyp_words else 1.0

    previous = list(range(len(hyp_words) + 1))
    for i, ref_word in enumerate(ref_words, start=1):
        current = [i]
        for j, hyp_word in enumerate(hyp_words, start=1):
            substitution = previous[j - 1] + (ref_word != hyp_word)
            insertion = current[j - 1] + 1
            deletion = previous[j] + 1
            current.append(min(substitution, insertion, deletion))
        previous = current
    return previous[-1] / len(ref_words)


def jaccard_similarity(ground_truth: set[str], prediction: set[str]) -> float:
    if not ground_truth and not prediction:
        return 1.0
    if not ground_truth and prediction:
        return 0.0
    union = ground_truth | prediction
    if not union:
        return 1.0
    return len(ground_truth & prediction) / len(union)


def text_score(pairs: list[tuple[str, str]]) -> float:
    if not pairs:
        return 1.0
    return sum(1 - word_error_rate(reference, hypothesis) for reference, hypothesis in pairs) / len(pairs)


def average_jaccard(pairs: list[tuple[set[str], set[str]]]) -> float:
    if not pairs:
        return 1.0
    return sum(jaccard_similarity(gt, pred) for gt, pred in pairs) / len(pairs)


def final_score(text: float, assertions: float, candidates: float) -> float:
    return 0.3 * text + 0.3 * assertions + 0.4 * candidates


__all__ = [
    "average_jaccard",
    "final_score",
    "jaccard_similarity",
    "text_score",
    "word_error_rate",
]
