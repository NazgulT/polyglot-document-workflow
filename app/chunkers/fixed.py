from __future__ import annotations

from typing import Any, Dict, List

import tiktoken


class FixedSizeChunker:
    """Split text into fixed-size character windows with overlap."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 0, encoding_name: str = "cl100k_base"):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be 0 or greater")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._encoding = tiktoken.get_encoding(encoding_name)

    def split_text(self, text: str) -> List[Dict[str, Any]]:
        """Return a list of chunks with text, char_offset, and token_count."""
        if text is None:
            text = ""

        step = self.chunk_size - self.chunk_overlap
        if step <= 0:
            raise ValueError("chunk_size must be greater than chunk_overlap")

        chunks: List[Dict[str, Any]] = []
        text_length = len(text)

        for start in range(0, text_length, step):
            window = text[start : start + self.chunk_size].strip()
            if not window:
                continue

            token_count = len(self._encoding.encode(window))
            chunks.append({
                "text": window,
                "char_offset": start,
                "token_count": token_count,
            })

            if start + self.chunk_size >= text_length:
                break

        return chunks
