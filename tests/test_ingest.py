# tests/test_ingest.py

import io
import pytest
from fastapi import status


class TestIngestEndpoint:

    def test_ingest_plain_text_success(self, client, sample_txt_file):
        response = client.post("/documents/ingest", files=[sample_txt_file])

        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body["status"] == "ready"
        assert body["mime_type"] == "text/plain"
        assert body["char_count"] > 0
        assert len(body["content_hash"]) == 64     # SHA-256 hex = 64 chars
        assert "doc_id" in body

    def test_ingest_duplicate_returns_existing(self, client, sample_txt_file, sample_txt_bytes):
        # First ingest
        client.post("/documents/ingest", files=[sample_txt_file])

        # Second ingest — same bytes
        second_file = ("file", ("copy.txt", io.BytesIO(sample_txt_bytes), "text/plain"))
        response = client.post("/documents/ingest", files=[second_file])

        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body["status"] == "duplicate"
        assert body["char_count"] is None

    def test_ingest_empty_file_rejected(self, client):
        empty_file = ("file", ("empty.txt", io.BytesIO(b""), "text/plain"))
        response = client.post("/documents/ingest", files=[empty_file])

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_ingest_disallowed_mime_type(self, client):
        fake_file = ("file", ("image.jpg", io.BytesIO(b"\xff\xd8\xff\xe0"), "image/jpeg"))
        response = client.post("/documents/ingest", files=[fake_file])

        assert response.status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE

    def test_ingest_oversized_file_rejected(self, client):
        big_bytes = b"x" * (21 * 1024 * 1024)     # 21 MB > 20 MB limit
        big_file = ("file", ("big.txt", io.BytesIO(big_bytes), "text/plain"))
        response = client.post("/documents/ingest", files=[big_file])

        assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE

    def test_content_hash_is_deterministic(self, client, sample_txt_bytes):
        """Same bytes uploaded twice must produce the same hash."""
        file_a = ("file", ("a.txt", io.BytesIO(sample_txt_bytes), "text/plain"))
        file_b = ("file", ("b.txt", io.BytesIO(sample_txt_bytes), "text/plain"))

        r1 = client.post("/documents/ingest", files=[file_a])
        r2 = client.post("/documents/ingest", files=[file_b])

        assert r1.json()["content_hash"] == r2.json()["content_hash"]

    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}