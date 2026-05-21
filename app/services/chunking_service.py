import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.chunkers import get_chunker
from app.embeddings import get_default_provider
from app.models.chunk import Chunk
from app.models.document import Document
from app.repositories.chunk import ChunkRepository
from app.schemas.chunk import ChunkingConfig, DocumentChunk


class ChunkingService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._provider = get_default_provider()
        self._repo = ChunkRepository(db)

    def process_document(
        self,
        doc_id: uuid.UUID,
        config: ChunkingConfig,
    ) -> list[DocumentChunk]:
        document = self._db.get(Document, doc_id)
        if document is None:
            return []

        if self._repo.exists_for_doc(doc_id):
            self._repo.delete_by_doc_id(doc_id)

        text = Path(document.extracted_path).read_text(encoding="utf-8")
        chunker = get_chunker(config)
        doc_chunks = chunker.split(text, doc_id)

        if not doc_chunks:
            return []

        embeddings = self._provider.embed_batch([dc.text for dc in doc_chunks])

        enriched: list[DocumentChunk] = [
            dc.model_copy(update={"chunk_index": i, "embedding": emb})
            for i, (dc, emb) in enumerate(zip(doc_chunks, embeddings))
        ]

        orm_chunks = [
            Chunk(
                chunk_id=dc.chunk_id,
                doc_id=dc.doc_id,
                chunk_index=dc.chunk_index,
                text=dc.text,
                char_offset=dc.char_offset,
                token_count=dc.token_count,
                embedding=dc.embedding,
            )
            for dc in enriched
        ]

        self._repo.bulk_insert(orm_chunks)
        return enriched
