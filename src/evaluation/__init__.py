"""Evaluation package.

Keep this package init lightweight. Do not import CLI modules here, because
`python -m src.evaluation.submission_validator` first imports this package and
then executes the submodule; eager-importing the submodule here triggers a
runpy RuntimeWarning.
"""

from .metrics import average_jaccard, final_score, jaccard_similarity, text_score, word_error_rate

__all__ = [
    "average_jaccard",
    "final_score",
    "jaccard_similarity",
    "text_score",
    "word_error_rate",
]


