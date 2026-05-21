

from logging import getLogger
from typing import Any, List
import uuid

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import text, select
from uvicorn import logging

from app.models.chunk import Chunk
from app.models.document import Document
from app.schemas.chunk import DocumentChunk
from app.schemas.search import SearchResult
from app.vector_store.base import VectorStoreError



logger = getLogger(__name__)


class VectorStore:
    def __init__(self, db: Session) -> None:
        self.db = db

    def upsert(self, chunks:List["DocumentChunk"]) -> int:

        """
        Insert chunks, updating all columns on conflict.

        ON CONFLICT (chunk_id) DO UPDATE means re-chunking a document
        safely overwrites old vectors without leaving orphan rows.
        """

        if not chunks:
            return 0
        try:
            
            rows: list[dict[str, Any]] = [
                {
                    "chunk_id": chunk.chunk_id,
                    "doc_id": chunk.doc_id,
                    "chunk_index": chunk.chunk_index,
                    "text": chunk.text,
                    "char_offset": chunk.char_offset,
                    "token_count": chunk.token_count,
                    "embedding": chunk.embedding
                }
                for chunk in chunks
            ]
    
            statement = pg_insert(Chunk).values(rows)
            statement = statement.on_conflict_do_update(
                index_elements=["chunk_id"],
                set_={
                    "chunk_index": statement.excluded.chunk_index,
                    "text": statement.excluded.text,
                    "char_offset": statement.excluded.char_offset,
                    "token_count": statement.excluded.token_count,
                    "embedding": statement.excluded.embedding
                },
            ) 

            result = self.db.execute(statement)
            count = result.rowcount
            self.db.commit()
            logger.info("Upserted %d chunks for doc_id=%s", count, chunks[0].doc_id)
            return count or 0
        except Exception as e:
            self.db.rollback()
            logger.info("Failed to upsert chunks for doc_id=%s: %s", chunks[0].doc_id, str(e))
            raise e  

    def search(self, query_embedding: list[float], top_k: int, filters: Any) -> List[DocumentChunk]:
        """
        Return the top_k chunks nearest to query_embedding by cosine similarity.

        Strategy:
        1. Let the HNSW index find the top_k candidates (fast approximate search)
        2. Filter out results below min_score in Python (at most top_k rows)
        3. Join Document for filename — single query, no N+1
        """

        try:
            # pgvector distance operator <=> returns cosine *distance* [0, 2].
            # We label it as distance here and convert to similarity after fetch.
            distance_expr = Chunk.embedding.cosine_distance(query_embedding).label("distance")

            stmt = (
                select(
                    Chunk.chunk_id,
                    Chunk.doc_id,
                    Chunk.chunk_index,
                    Chunk.char_offset,
                    Chunk.text,
                    Document.filename,
                    distance_expr,
                )
                .join(Document, Chunk.doc_id == Document.doc_id)
                .order_by(distance_expr)   # ascending distance = descending similarity
                .limit(top_k)
            )

            # Apply doc_id filter at SQL level
            if filters.doc_ids:
                stmt = stmt.where(Chunk.doc_id.in_(filters.doc_ids))

            rows = self._db.execute(stmt).fetchall()

        except Exception as exc:
            logger.exception("Search query failed")
            raise VectorStoreError(f"Search failed: {exc}") from exc

        results: list[SearchResult] = []
        for row in rows:
            # Convert distance [0, 2] → similarity [−1, 1], then clamp to [0, 1]
            similarity = max(0.0, 1.0 - float(row.distance))

            if similarity < filters.min_score:
                continue  # Post-fetch filter — see hint above

            results.append(
                SearchResult(
                    chunk_id=row.chunk_id,
                    doc_id=row.doc_id,
                    chunk_index=row.chunk_index,
                    char_offset=row.char_offset,
                    text=row.text,
                    score=round(similarity, 4),
                    filename=row.filename,
                )
            )

        return results

    # ──────────────────────────────────────────────────────────────────────────
    # Delete
    # ──────────────────────────────────────────────────────────────────────────

    def delete_by_doc_id(self, doc_id: uuid.UUID) -> int:
        """Delete all chunks for a document. Used before re-chunking."""
        try:
            result = self._db.execute(
                text("DELETE FROM chunks WHERE doc_id = :doc_id"),
                {"doc_id": str(doc_id)},
            )
            self._db.commit()
            count = result.rowcount
            logger.info("Deleted %d chunks for doc_id=%s", count, doc_id)
            return count
        except Exception as exc:
            self._db.rollback()
            raise VectorStoreError(f"Delete failed: {exc}") from exc