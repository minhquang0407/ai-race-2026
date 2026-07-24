import pytest

from src.evaluation.metrics import average_jaccard, final_score, jaccard_similarity, text_score, word_error_rate


def test_word_error_rate_exact_and_substitution():
    assert word_error_rate("đau ngực", "đau ngực") == 0
    assert word_error_rate("đau ngực", "đau bụng") == pytest.approx(0.5)


def test_jaccard_similarity():
    assert jaccard_similarity({"A", "B"}, {"B", "C"}) == pytest.approx(1 / 3)
    assert jaccard_similarity(set(), set()) == 1.0


def test_average_and_final_score():
    assert text_score([("A B", "A B")]) == 1.0
    assert average_jaccard([({"x"}, {"x", "y"})]) == pytest.approx(0.5)
    assert final_score(1.0, 0.5, 0.25) == pytest.approx(0.55)
