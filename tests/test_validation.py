import pytest

from src.extraction.chunking import TextChunk
from src.extraction.validation import local_to_global, require_valid_span, validate_span


def test_validate_span_exact_match():
    text = "Bệnh nhân ho và sốt."
    start = text.index("ho")
    end = start + len("ho")
    assert validate_span(text, "ho", start, end)
    assert not validate_span(text, "sốt", start, end)


def test_require_valid_span_raises_on_mismatch():
    with pytest.raises(ValueError):
        require_valid_span("abc", "ab", 1, 3)


def test_local_to_global_mapping():
    source = "Bệnh nhân ho và sốt."
    chunk = TextChunk(source[10:19], 10, 19, 0)
    assert local_to_global(0, 2, chunk) == (10, 12)


def test_local_to_global_rejects_invalid_coordinates():
    chunk = TextChunk("abc", 5, 8, 0)
    for start, end in [(-1, 2), (1, 1), (2, 1), (0, 4)]:
        with pytest.raises(ValueError):
            local_to_global(start, end, chunk)
