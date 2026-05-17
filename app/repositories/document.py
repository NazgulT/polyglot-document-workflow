# app/repositories/document.py

import uuid
import pathlib
from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.document import Document
from app.schemas.document import DocumentRecord, DocumentStatus
from app.config import get_settings


class DocumentRepository:
    """
    All database access for the documents table lives here.

    Keeping DB logic out of routes and extractors makes it trivial to
    swap the storage backend (e.g. to an async session in Step 5) or
    mock it in tests without touching business logic.
    """

    def __init__(self, db: Session) -> None:
        self._db = db

    def find_by_hash(self, content_hash: str) -> Document | None:
        return (
            self._db.query(Document)
            .filter(Document.content_hash == content_hash)
            .first()
        )

    def create(
        self,
        *,
        filename: str,
        mime_type: str,
        content_hash: str,
        extracted_text: str,
    ) -> Document:
        settings = get_settings()

        # Write extracted text to disk (keeps large blobs off the DB)
        text_path = self._write_text_file(
            content_hash=content_hash,
            text=extracted_text,
            base_dir=settings.extracted_text_dir,
        )

        doc = Document(
            doc_id=uuid.uuid4(),
            filename=filename,
            mime_type=mime_type,
            content_hash=content_hash,
            char_count=len(extracted_text),
            extracted_path=str(text_path),
            status=DocumentStatus.READY,
            created_at=datetime.now(timezone.utc),
        )

        try:
            self._db.add(doc)
            self._db.commit()
            self._db.refresh(doc)
        except IntegrityError:
            # Race condition: another request inserted the same hash concurrently.
            # The UNIQUE constraint caught it — roll back and treat as duplicate.
            self._db.rollback()
            existing = self.find_by_hash(content_hash)
            return existing  # type: ignore[return-value]

        return doc

    @staticmethod
    def _write_text_file(
        content_hash: str,
        text: str,
        base_dir: str,
    ) -> pathlib.Path:
        """
        Persist extracted text as a flat file named by its content hash.

        Using the hash as the filename means writes are also idempotent —
        re-writing the same content produces the same file at the same path.
        """
        directory = pathlib.Path(base_dir)
        directory.mkdir(parents=True, exist_ok=True)

        text_path = directory / f"{content_hash}.txt"
        text_path.write_text(text, encoding="utf-8")

        return text_path