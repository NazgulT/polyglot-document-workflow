from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from app.schemas.chunk import DocumentChunk
else:
    DocumentChunk = Any


class ChunkingStrategy(Protocol):
    def split(self, text: str, doc_id: uuid.UUID) -> list[DocumentChunk]:
        ...

class ChunkingError(Exception):
    """Raised when text cannot be chunked according to the specified strategy."""
