import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.chunkers import get_chunker
from app.chunkers.fixed import FixedSizeChunker
from app.embeddings import get_default_provider
from app.models.chunk import Chunk
from app.models.document import Document
from app.repositories.chunk import ChunkRepository
from app.schemas.chunk import ChunkingConfig


def _normalise(chunker, text: str) -> list[dict]:
    """Return list[dict] with text/char_offset/token_count regardless of chunker type."""
    if isinstance(chunker, FixedSizeChunker):
        return chunker.split_text(text)

    result = chunker.chunk(text)
    if not result:
        return []

    if isinstance(result[0], str):
        # RecursiveCharacterChunker returns plain strings; rebuild offsets by scanning.
        normalised: list[dict] = []
        scan_from = 0
        for chunk_text in result:
            offset = text.find(chunk_text, scan_from)
            normalised.append({
                "text": chunk_text,
                "char_offset": max(offset, 0),
                "token_count": 0,
            })
            if offset >= 0:
                scan_from = offset + len(chunk_text)
        return normalised

    # SentenceWindowChunker returns list[dict] with text + char_offset but no token_count.
    return [
        {"text": c["text"], "char_offset": c.get("char_offset", 0), "token_count": 0}
        for c in result
    ]


class ChunkingService:
    def __init__(self, db: Session) -> None:
        self._db = db
        self._provider = get_default_provider()
        self._repo = ChunkRepository(db)

    def process_document(
        self,
        doc_id: uuid.UUID,
        config: ChunkingConfig,
    ) -> list[Chunk]:
        document = self._db.get(Document, doc_id)
        if document is None:
            return []

        if self._repo.exists_for_doc(doc_id):
            self._repo.delete_by_doc_id(doc_id)

        extracted_text = Path(document.extracted_path).read_text(encoding="utf-8")
        chunker = get_chunker(config)
        raw = _normalise(chunker, extracted_text)

        embeddings = self._provider.embed_batch([r["text"] for r in raw])

        orm_chunks = [
            Chunk(
                chunk_id=uuid.uuid4(),
                doc_id=doc_id,
                chunk_index=i,
                text=r["text"],
                char_offset=r["char_offset"],
                token_count=r["token_count"],
                embedding=emb,
            )
            for i, (r, emb) in enumerate(zip(raw, embeddings))
        ]

        self._repo.bulk_insert(orm_chunks)
        return orm_chunks
