# app/main.py

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routers import ingest
from app.routers import chunks


def create_app() -> FastAPI:
    app = FastAPI(
        title="Document Ingestion Pipeline",
        version="1.0.0",
        description="Step 1 of the Polyglot Document Workflow",
    )

    app.include_router(ingest.router)
    app.include_router(chunks.router)

    @app.get("/health", tags=["ops"])
    def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()