# app/routers/search.py

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.embeddings import get_default_provider
from app.schemas.search import (
    SearchQuery,
    SearchResponse,
    UpsertRequest,
    UpsertResponse,
)
from app.services.search_service import SearchService
from app.vector_store import get_vector_store
from app.vector_store.base import VectorStoreError

router = APIRouter(prefix="/chunks", tags=["search"])


# ── Dependency wiring ─────────────────────────────────────────────────────────

def get_search_service(db: Session = Depends(get_db)) -> SearchService:
    """
    Assembles SearchService with its dependencies.

    Called once per request by FastAPI's dependency injection system.
    The embedding provider is a cached singleton (see app/embeddings/__init__.py)
    so the model is loaded only on first request, not on every request.
    """
    return SearchService(
        vector_store=get_vector_store(db),
        embedding_provider=get_default_provider(),
        db=db,
    )


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post(
    "/upsert",
    response_model=UpsertResponse,
    status_code=status.HTTP_200_OK,
    summary="Push a document's chunks into the vector store",
    description=(
        "Loads chunks from the database (populated by POST /documents/{doc_id}/chunks) "
        "and upserts them into pgvector. Idempotent — safe to call multiple times."
    ),
)

def upsert_chunks(
    body: UpsertRequest,
    service: SearchService = Depends(get_search_service),
) -> UpsertResponse:
    try:
        return service.upsert_for_document(body.doc_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except VectorStoreError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Vector store error: {exc}",
        )


@router.post(
    "/search",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Semantic search over ingested documents",
    description=(
        "Embeds the query string and returns the top-K most semantically "
        "similar chunks. Optionally filter by document IDs or minimum score."
    ),
)

def search_chunks(
    body: SearchQuery,
    service: SearchService = Depends(get_search_service),
) -> SearchResponse:
    try:
        return service.search(body)
    except VectorStoreError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Vector store error: {exc}",
        )