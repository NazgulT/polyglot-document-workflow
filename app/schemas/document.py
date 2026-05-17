# app/schemas/document.py

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, ConfigDict


class DocumentStatus(StrEnum):
    PENDING   = "pending"     # record created, extraction in progress
    READY     = "ready"       # text extracted and persisted
    DUPLICATE = "duplicate"   # content hash already exists
    FAILED    = "failed"      # extraction raised an unrecoverable error


class IngestResponse(BaseModel):
    """
    Returned immediately after a successful ingest request.

    The `status` field tells the caller whether this was a new document
    or a duplicate. Downstream jobs (embedding, metadata sync) key on `doc_id`.
    """

    doc_id:       uuid.UUID
    filename:     str
    mime_type:    str
    status:       DocumentStatus
    content_hash: str          = Field(description="SHA-256 hex digest of raw file bytes")
    char_count:   int | None   = Field(default=None, description="Characters extracted; null on duplicate")
    created_at:   datetime
    message:      str

    model_config = ConfigDict(from_attributes=True)


class DocumentRecord(BaseModel):
    """Internal representation used between layers. Not exposed directly."""

    doc_id:         uuid.UUID
    filename:       str
    mime_type:      str
    content_hash:   str
    char_count:     int
    extracted_path: str        # filesystem or object-storage path
    status:         DocumentStatus
    created_at:     datetime

    model_config = ConfigDict(from_attributes=True)