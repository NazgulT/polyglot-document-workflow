from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session

from app.models.chunk import Chunk

if TYPE_CHECKING:
    from app.schemas.chunk import DocumentChunk


class ChunkRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def bulk_insert(self, chunks: list["DocumentChunk"]) -> int:
        if not chunks:
            return 0

        first_chunk = chunks[0]
        if isinstance(first_chunk, Chunk):
            self.db.bulk_save_objects(chunks)
        else:
            def to_record(chunk: "DocumentChunk") -> dict:
                if isinstance(chunk, dict):
                    return chunk
                if hasattr(chunk, "dict"):
                    return chunk.dict(exclude_none=True)
                return {k: v for k, v in vars(chunk).items() if not k.startswith("_")}

            records = [to_record(chunk) for chunk in chunks]
            self.db.execute(insert(Chunk), records)

        self.db.commit()
        return len(chunks)

    def find_by_doc_id(self, doc_id: uuid.UUID) -> list[Chunk]:
        stmt = select(Chunk).where(Chunk.doc_id == doc_id).order_by(Chunk.chunk_index)
        return self.db.execute(stmt).scalars().all()

    def delete_by_doc_id(self, doc_id: uuid.UUID) -> int:
        stmt = delete(Chunk).where(Chunk.doc_id == doc_id)
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount or 0

    def exists_for_doc(self, doc_id: uuid.UUID) -> bool:
        stmt = select(Chunk.chunk_id).where(Chunk.doc_id == doc_id).limit(1)
        return self.db.execute(stmt).scalar_one_or_none() is not None
