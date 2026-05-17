# app/routers/ingest.py

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_settings, Settings
from app.database import get_db
from app.extractors import detect_mime_type, get_extractor
from app.extractors.base import ExtractionError
from app.repositories.document import DocumentRepository
from app.schemas.document import IngestResponse, DocumentStatus

router = APIRouter(prefix="/documents", tags=["ingestion"])


@router.post(
    "/ingest",
    response_model=IngestResponse,
    status_code=status.HTTP_200_OK,
    summary="Ingest a document",
    description=(
        "Upload a PDF, DOCX, or plain-text file. "
        "The pipeline detects its type, extracts text, deduplicates by content hash, "
        "and persists the record. Returns immediately with the document status."
    ),
)
def ingest_document(
    file: UploadFile = File(..., description="PDF, DOCX, or plain text file"),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> IngestResponse:

    # ── 1. Read and size-check ───────────────────────────────────────────────
    raw_bytes = file.file.read()

    if len(raw_bytes) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                f"File size {len(raw_bytes):,} bytes exceeds the "
                f"{settings.max_upload_bytes:,}-byte limit."
            ),
        )

    if len(raw_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded file is empty.",
        )

    # ── 2. MIME detection (from bytes, not filename) ─────────────────────────
    mime_type = detect_mime_type(raw_bytes)

    if mime_type not in settings.allowed_mime_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"MIME type '{mime_type}' is not supported. "
                f"Allowed: {settings.allowed_mime_types}"
            ),
        )

    # ── 3. Content fingerprint ───────────────────────────────────────────────
    from app.utils.fingerprint import sha256_hex
    content_hash = sha256_hex(raw_bytes)

    # ── 4. Deduplication check ───────────────────────────────────────────────
    repo = DocumentRepository(db)
    existing = repo.find_by_hash(content_hash)

    if existing is not None:
        return IngestResponse(
            doc_id=existing.doc_id,
            filename=existing.filename,
            mime_type=existing.mime_type,
            status=DocumentStatus.DUPLICATE,
            content_hash=existing.content_hash,
            char_count=None,                    # Don't re-report on duplicate
            created_at=existing.created_at,
            message="Document already exists. Returning existing record.",
        )

    # ── 5. Text extraction ───────────────────────────────────────────────────
    try:
        extractor = get_extractor(mime_type)
        extracted_text = extractor.extract(raw_bytes)
    except ExtractionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Text extraction failed: {exc}",
        )

    # ── 6. Persist ───────────────────────────────────────────────────────────
    doc = repo.create(
        filename=file.filename or "unknown",
        mime_type=mime_type,
        content_hash=content_hash,
        extracted_text=extracted_text,
    )

    return IngestResponse(
        doc_id=doc.doc_id,
        filename=doc.filename,
        mime_type=doc.mime_type,
        status=DocumentStatus.READY,
        content_hash=doc.content_hash,
        char_count=doc.char_count,
        created_at=doc.created_at,
        message="Document ingested successfully.",
    )