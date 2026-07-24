"""Offset validation helpers for extraction outputs."""

from __future__ import annotations

from .chunking import TextChunk


def validate_span(source_text: str, text: str, start: int, end: int) -> bool:
    """Return True when a half-open span exactly matches the expected text."""

    if start < 0 or end < 0 or start >= end or end > len(source_text):
        return False
    return source_text[start:end] == text


def require_valid_span(source_text: str, text: str, start: int, end: int) -> None:
    """Raise a descriptive error when a span does not match its source text."""

    if not validate_span(source_text, text, start, end):
        observed = source_text[start:end] if 0 <= start <= end <= len(source_text) else None
        raise ValueError(
            f"invalid span [{start}, {end}) for {text!r}; observed {observed!r}"
        )


def local_to_global(local_start: int, local_end: int, chunk: TextChunk) -> tuple[int, int]:
    """Map local chunk coordinates to source-level coordinates."""

    if local_start < 0 or local_end < 0:
        raise ValueError("local coordinates must be non-negative")
    if local_start >= local_end:
        raise ValueError("local coordinates must satisfy start < end")
    if local_end > len(chunk.text):
        raise ValueError("local coordinates exceed chunk length")
    return chunk.start + local_start, chunk.start + local_end


__all__ = ["local_to_global", "require_valid_span", "validate_span"]
