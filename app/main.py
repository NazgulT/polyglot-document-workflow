# app/main.py

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routers import search
from app.routers import ingest
from app.routers import chunks


def create_app() -> FastAPI:
    app = FastAPI(
        title="Polyglot Document Workflow, steps 1-3",
        version="3.0.0",
        description="Document ingestion, chunking and semantic search of the Polyglot Document Workflow" \
        "backed by PostgreSQL and pgvector.",
    )

    app.include_router(ingest.router)
    app.include_router(chunks.router)
    app.include_router(search.router)

    @app.get("/health", tags=["ops"])
    def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()