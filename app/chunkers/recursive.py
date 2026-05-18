from __future__ import annotations

from typing import List


class RecursiveCharacterChunker:
    """Chunk text recursively by character with prioritized separators."""

    separators: List[str] = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, chunk_size: int) -> None:
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> List[str]:
        return self._chunk_text(text, self.chunk_size, self.separators)

    def _chunk_text(
        self,
        text: str,
        max_size: int,
        separators: List[str],
    ) -> List[str]:
        if not text:
            return []

        if len(text) <= max_size:
            return [text]

        if not separators:
            return [text]

        separator = separators[0]
        if separator == "":
            return [text[i : i + max_size] for i in range(0, len(text), max_size)]

        parts = self._split_with_separator(text, separator)
        if len(parts) <= 1:
            return self._chunk_text(text, max_size, separators[1:])

        expanded_chunks: List[str] = []
        for part in parts:
            if not part:
                continue
            if len(part) <= max_size:
                expanded_chunks.append(part)
            else:
                expanded_chunks.extend(
                    self._chunk_text(part, max_size, separators[1:])
                )

        return self._merge_chunks(expanded_chunks, max_size)

    @staticmethod
    def _split_with_separator(text: str, separator: str) -> List[str]:
        parts: List[str] = []
        start = 0
        while True:
            index = text.find(separator, start)
            if index == -1:
                remainder = text[start:]
                if remainder:
                    parts.append(remainder)
                break
            end = index + len(separator)
            parts.append(text[start:end])
            start = end
        return parts

    @staticmethod
    def _merge_chunks(chunks: List[str], max_size: int) -> List[str]:
        merged: List[str] = []
        current_chunk = ""

        for chunk in chunks:
            if not current_chunk:
                current_chunk = chunk
                continue

            if len(current_chunk) + len(chunk) <= max_size:
                current_chunk += chunk
            else:
                merged.append(current_chunk)
                current_chunk = chunk

        if current_chunk:
            merged.append(current_chunk)

        return merged
