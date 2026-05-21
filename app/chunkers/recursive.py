from __future__ import annotations

from typing import List
import uuid

from app.chunkers.base import ChunkingError
from app.schemas.chunk import DocumentChunk


class RecursiveCharacterChunker:
    """Chunk text recursively by character with prioritized separators."""

    separators: List[str] = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, chunk_size: int) -> None:
        self.chunk_size = chunk_size

    def split(self, text: str, doc_id: uuid.UUID) -> List[DocumentChunk]:
        return self._chunk_text(text, self.chunk_size, self.separators, doc_id)

    def _chunk_text(
        self,
        text: str,
        max_size: int,
        separators: List[str],
        doc_id: uuid.UUID
    ) -> List[DocumentChunk]:
        if not text:
            return []

        if len(text) <= max_size:
            return [DocumentChunk(text=text, char_offset=0, token_count=0, doc_id=doc_id)]

        if not separators:
            return [DocumentChunk(text=text, char_offset=0, token_count=0, doc_id=doc_id)]

        separator = separators[0]
        if separator == "":
            return [DocumentChunk(text=text[i : i + max_size], char_offset=i, token_count=0, doc_id=doc_id) for i in range(0, len(text), max_size)]


        try:

            parts = self._split_with_separator(text, separator)
            if len(parts) <= 1:
                return self._chunk_text(text, max_size, separators[1:], doc_id)

            expanded_chunks: List[DocumentChunk] = []
            for part in parts:
                if not part:
                    continue
                if len(part) <= max_size:
                    expanded_chunks.append(DocumentChunk(text=part, char_offset=0, token_count=0, doc_id=doc_id))
                else:
                    expanded_chunks.extend(
                        self._chunk_text(part, max_size, separators[1:], doc_id)
                    )
        except Exception as e:
            raise ChunkingError(f"Error during Recursive Character chunking: {e}")

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
    def _merge_chunks(chunks: List[DocumentChunk], max_size: int) -> List[DocumentChunk]:
        merged: List[DocumentChunk] = []
        current_chunk = None

        for chunk in chunks:
            if not current_chunk:
                current_chunk = chunk
                continue

            if len(current_chunk.text) + len(chunk.text) <= max_size:
                current_chunk = DocumentChunk(
                    text=current_chunk.text + chunk.text,
                    char_offset=current_chunk.char_offset,
                    token_count=current_chunk.token_count + chunk.token_count,
                    doc_id=current_chunk.doc_id
                )
            else:
                merged.append(current_chunk)
                current_chunk = chunk

        if current_chunk:
            merged.append(current_chunk)

        return merged
