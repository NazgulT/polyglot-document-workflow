# app/models/document.py

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Document(Base):
    __tablename__ = "documents"

    doc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    filename: Mapped[str]       = mapped_column(String(512), nullable=False)
    mime_type: Mapped[str]      = mapped_column(String(128), nullable=False)
    content_hash: Mapped[str]   = mapped_column(String(64), nullable=False, unique=True, index=True)
    char_count: Mapped[int]     = mapped_column(Integer, nullable=False)
    extracted_path: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str]         = mapped_column(String(32), nullable=False, default="ready")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )