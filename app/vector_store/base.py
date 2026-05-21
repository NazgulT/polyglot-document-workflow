

from typing import List, Protocol, runtime_checkable

import uuid

from app.schemas.chunk import DocumentChunk
from app.schemas.search import SearchFilters, SearchResult

@runtime_checkable
class VectorStore(Protocol):
    """Interface for vector stores."""
    """
    Storage and retrieval contract for embedded document chunks.

    Implementations are responsible for:
    - Persisting chunk text, metadata, and embedding vectors
    - Executing approximate nearest-neighbour search with optional filters
    - Deleting all chunks belonging to a document

    Implementations are NOT responsible for:
    - Embedding queries (that is SearchService's job)
    - Chunking documents (that is ChunkingService's job)
    - HTTP concerns of any kind
    """

    def upsert(self, documents: List[DocumentChunk]) -> int:
        """Add or update vectors in the store.
        Return the number of vectors upserted."""
        ...

    def search(self, query_embedding: list[float], top_k: int, filters: SearchFilters) -> List[SearchResult]:
        """Search for similar vectors in the store."""
        ...

    def delete_by_doc_id(self, doc_id: uuid.UUID) -> int:
        """Delete vectors associated with a document ID.
        Return the number of vectors deleted."""
        ...

class VectorStoreError(Exception):
    """Raised when an error occurs in the vector store."""