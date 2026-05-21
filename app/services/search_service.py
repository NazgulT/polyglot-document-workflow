


from time import time

from fastapi import logger
from sqlalchemy.orm import Session

from app.embeddings.base import EmbeddingProvider
from app.schemas.search import SearchQuery, SearchResponse, UpsertResponse
from app.vector_store.base import VectorStore

from app.repositories.chunk import ChunkRepository

import uuid


class SearchService:
    def __init__(self, db: Session, vector_store: VectorStore, embedding_provider: EmbeddingProvider):
        self.db = db
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider

    def search(self, query: SearchQuery) -> SearchResponse:

        """
        Orchestrates query embedding and vector store retrieval.

        Separating this from the router keeps timing, error handling,
        and provider-swapping logic out of HTTP concerns.
        """

        t0 = time.perf_counter()

        query_embedding = self.embedding_provider.embed_batch([query.query])[0]
        embedding_ms = (time.perf_counter() - t0) * 1000
        results = self._store.search(
            query_embedding=query_embedding,
            top_k=query.top_k,
            filters=query.filters,
        )

        logger.info(
            "Search complete: %d results in %.1fms embedding + DB query",
            len(results),
            embedding_ms,
        )

        return SearchResponse(
            query=query.query,
            results=results,
            result_count=len(results),
            query_embedding_ms=round(embedding_ms, 2),
        )

    def upsert_for_document(self, doc_id: uuid.UUID) -> UpsertResponse:
        """
        Load chunks from the DB and push them into the vector store.

        This is idempotent: calling it twice on the same document produces
        the same vector store state, because PgVectorStore.upsert uses
        ON CONFLICT DO UPDATE.
        """
        repo = ChunkRepository(self._db)
        chunks = repo.find_by_doc_id(doc_id)

        if not chunks:
            raise ValueError(
                f"No chunks found for doc_id={doc_id}. "
                "Run POST /documents/{doc_id}/chunks first."
            )

        # Confirm all chunks have embeddings — guard against partial Step 2 runs
        missing = [c for c in chunks if c.embedding is None]
        if missing:
            raise ValueError(
                f"{len(missing)} of {len(chunks)} chunks are missing embeddings. "
                "Re-run the chunking step."
            )

        count = self._store.upsert(chunks)

        return UpsertResponse(
            doc_id=doc_id,
            chunks_upserted=count,
            message=f"Successfully upserted {count} chunks into the vector store.",
        )