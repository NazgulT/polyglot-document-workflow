from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.document import Document
from app.schemas.chunk import ChunkingConfig as ServiceConfig
from app.services.chunking_service import ChunkingService

router = APIRouter()


class ChunkingConfig(BaseModel):
    strategy: str = Field(..., description="Chunking strategy to use")
    embedding_dimensions: int = Field(..., gt=0, description="Embedding vector dimensions")
    chunk_size: Optional[int] = Field(1000, gt=0, description="Approximate maximum size of each chunk")
    overlap: Optional[int] = Field(0, ge=0, description="Number of characters to overlap between chunks")


class ChunkingResponse(BaseModel):
    doc_id: UUID
    chunk_count: int
    strategy: str
    embedding_dimensions: int
    message: str


@router.post(
    "/documents/{doc_id}/chunks",
    response_model=ChunkingResponse,
    summary="Create chunks for a document",
)
def create_document_chunks(
    doc_id: UUID = Path(..., description="Document ID to chunk"),
    config: ChunkingConfig = ...,
    db: Session = Depends(get_db),
) -> ChunkingResponse:
    if db.get(Document, doc_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    service_config = ServiceConfig(
        strategy=config.strategy.strip(),
        chunk_size=config.chunk_size,
        chunk_overlap=config.overlap,
    )

    chunks = ChunkingService(db).process_document(doc_id, service_config)

    return ChunkingResponse(
        doc_id=doc_id,
        chunk_count=len(chunks),
        strategy=service_config.strategy,
        embedding_dimensions=config.embedding_dimensions,
        message="Document chunked and embedded successfully.",
    )
