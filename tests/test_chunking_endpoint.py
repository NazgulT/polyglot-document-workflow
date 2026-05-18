# tests/test_chunking_endpoint.py
#
# Integration tests for POST /documents/{doc_id}/chunks.
# All tests use the `client` and `db_session` fixtures from conftest.py.
# Importing Chunk here ensures its table is created by the session-scoped
# setup_test_db fixture (Base.metadata.create_all includes it at collection time).

import io
import uuid

import pytest
from sqlalchemy import select

from app.models.chunk import Chunk  # noqa: F401 — registers table with Base.metadata


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_content() -> bytes:
    """Return unique plain-text bytes so every call produces a new content hash."""
    filler = (
        "The quick brown fox jumps over the lazy dog. "
        "Pack my box with five dozen liquor jugs. "
        "How vexingly quick daft zebras jump. "
        "The five boxing wizards jump quickly. "
    ) * 4
    return f"[{uuid.uuid4()}] {filler}".encode()


def _ingest(client, content: bytes | None = None) -> str:
    """POST to /documents/ingest and return doc_id."""
    raw = content if content is not None else _make_content()
    files = {"file": ("sample.txt", io.BytesIO(raw), "text/plain")}
    resp = client.post("/documents/ingest", files=files)
    assert resp.status_code == 200, resp.text
    return resp.json()["doc_id"]


CHUNK_PAYLOAD = {
    "strategy": "fixed",
    "embedding_dimensions": 384,
    "chunk_size": 200,
    "overlap": 50,
}


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_chunk_document_success(client):
    doc_id = _ingest(client)
    resp = client.post(f"/documents/{doc_id}/chunks", json=CHUNK_PAYLOAD)

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["doc_id"] == doc_id
    assert body["strategy"] == CHUNK_PAYLOAD["strategy"]
    assert body["chunk_count"] > 0, "Expected at least one chunk to be created"


def test_chunk_unknown_doc_returns_404(client):
    fake_id = str(uuid.uuid4())
    resp = client.post(f"/documents/{fake_id}/chunks", json=CHUNK_PAYLOAD)

    assert resp.status_code == 404, (
        f"Expected 404 for unknown doc, got {resp.status_code}: {resp.text}"
    )


def test_reprocessing_replaces_chunks_not_appends(client):
    doc_id = _ingest(client)

    first = client.post(f"/documents/{doc_id}/chunks", json=CHUNK_PAYLOAD)
    assert first.status_code == 200, first.text
    first_count = first.json()["chunk_count"]
    assert first_count > 0

    second = client.post(f"/documents/{doc_id}/chunks", json=CHUNK_PAYLOAD)
    assert second.status_code == 200, second.text
    second_count = second.json()["chunk_count"]

    assert second_count == first_count, (
        f"Re-processing doubled chunks: {first_count} → {second_count}. "
        "Old chunks must be deleted before inserting new ones."
    )


def test_embeddings_have_correct_dimensions(client, db_session):
    doc_id = _ingest(client)
    resp = client.post(f"/documents/{doc_id}/chunks", json=CHUNK_PAYLOAD)
    assert resp.status_code == 200, resp.text

    chunks = db_session.execute(
        select(Chunk).where(Chunk.doc_id == uuid.UUID(doc_id))
    ).scalars().all()

    assert len(chunks) > 0, "No chunk rows found in DB after chunking"
    for chunk in chunks:
        assert chunk.embedding is not None, f"Chunk {chunk.chunk_id} has no embedding"
        assert len(chunk.embedding) == 384, (
            f"Expected 384-dim embedding, got {len(chunk.embedding)}"
        )
