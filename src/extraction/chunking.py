"""Semantic chunking utilities that preserve original offsets."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    text: str
    start: int
    end: int
    index: int

    def validate_against(self, source_text: str) -> None:
        if self.start < 0 or self.end < self.start or self.end > len(source_text):
            raise ValueError("chunk span is out of bounds")
        if source_text[self.start:self.end] != self.text:
            raise ValueError("chunk text does not match source span")


class SemanticChunker:
    """Regex-free span chunker focused on offset safety.

    The chunker never normalizes, strips, or rewrites the input text. It only
    returns slices into the original string.
    """

    def __init__(
        self,
        target_size: int = 200,
        min_size: int = 150,
        max_size: int = 250,
        overlap_chars: int = 0,
    ) -> None:
        if not (0 <= overlap_chars < max_size):
            raise ValueError("overlap_chars must satisfy 0 <= overlap_chars < max_size")
        if min_size <= 0 or target_size <= 0 or max_size <= 0:
            raise ValueError("chunk sizes must be positive")
        if min_size > target_size or target_size > max_size:
            raise ValueError("sizes must satisfy min_size <= target_size <= max_size")
        self.target_size = target_size
        self.min_size = min_size
        self.max_size = max_size
        self.overlap_chars = overlap_chars

    def split(self, source_text: str) -> list[TextChunk]:
        if source_text == "":
            return []

        chunks: list[TextChunk] = []
        start = 0
        text_len = len(source_text)

        while start < text_len:
            end = self._choose_end(source_text, start)
            if end <= start:
                end = min(start + self.max_size, text_len)
            chunks.append(TextChunk(source_text[start:end], start, end, len(chunks)))
            if end >= text_len:
                break
            start = self._next_start(source_text, start, end)

        for chunk in chunks:
            chunk.validate_against(source_text)
        return chunks

    def _choose_end(self, text: str, start: int) -> int:
        text_len = len(text)
        remaining = text_len - start
        if remaining <= self.max_size:
            return text_len

        hard_limit = min(start + self.max_size, text_len)
        target = min(start + self.target_size, hard_limit)
        min_end = min(start + self.min_size, hard_limit)

        newline = self._find_last_newline_boundary(text, min_end, hard_limit)
        if newline is not None:
            return newline

        sentence = self._find_last_sentence_boundary(text, min_end, hard_limit)
        if sentence is not None:
            return sentence

        comma = self._find_last_char_boundary(text, min_end, hard_limit, {",", ":"})
        if comma is not None:
            return comma

        word = self._find_last_whitespace_boundary(text, min_end, hard_limit)
        if word is not None:
            return word

        return target

    def _next_start(self, text: str, start: int, end: int) -> int:
        if self.overlap_chars == 0:
            return end
        next_start = max(start + 1, end - self.overlap_chars)
        while next_start < end and not text[next_start].isspace() and not text[next_start - 1].isspace():
            next_start += 1
        return min(next_start, end)

    @staticmethod
    def _find_last_newline_boundary(text: str, min_end: int, hard_limit: int) -> int | None:
        for i in range(hard_limit - 1, min_end - 1, -1):
            if text[i] == "\n":
                return i + 1
        return None

    @staticmethod
    def _find_last_sentence_boundary(text: str, min_end: int, hard_limit: int) -> int | None:
        for i in range(hard_limit - 1, min_end - 1, -1):
            if text[i] in ".!?;" and i + 1 < len(text) and text[i + 1].isspace():
                # Avoid cutting decimal-like expressions such as 0.4.
                if i > 0 and i + 1 < len(text) and text[i - 1].isdigit() and text[i + 1].isdigit():
                    continue
                return i + 1
        return None

    @staticmethod
    def _find_last_char_boundary(text: str, min_end: int, hard_limit: int, chars: set[str]) -> int | None:
        for i in range(hard_limit - 1, min_end - 1, -1):
            if text[i] in chars and i + 1 < len(text) and text[i + 1].isspace():
                return i + 1
        return None

    @staticmethod
    def _find_last_whitespace_boundary(text: str, min_end: int, hard_limit: int) -> int | None:
        for i in range(hard_limit - 1, min_end - 1, -1):
            if text[i].isspace():
                return i + 1
        return None


__all__ = ["SemanticChunker", "TextChunk"]
