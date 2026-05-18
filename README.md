# Polyglot Document Workflow

A document ingestion and chunking pipeline built with **FastAPI** and **PostgreSQL + pgvector** that accepts PDF, DOCX, and plain-text files, extracts their text, splits it into semantic chunks, and stores vector embeddings — designed as the Python backend of a polyglot RAG (Retrieval-Augmented Generation) system.

---

## What It Does

**Phase 1 — Ingestion:** Upload a document and the pipeline will:

1. **Validate** file size and detect MIME type from raw bytes (never from filename)
2. **Fingerprint** content with SHA-256 and skip storage if the document already exists
3. **Extract** clean UTF-8 text using a format-specific extractor (PDF via PyMuPDF, DOCX via python-docx, plain text natively)
4. **Persist** the record in PostgreSQL and return `doc_id`, `status`, and `char_count`

**Phase 2 — Chunking & Embedding:** POST to chunk an ingested document and the pipeline will:

5. **Split** extracted text into overlapping chunks using one of three strategies
6. **Embed** each chunk via `all-MiniLM-L6-v2` (384-dim, local, no API key needed)
7. **Store** chunks with `char_offset`, `token_count`, and a `vector(384)` embedding in Postgres

| Supported Format | MIME Type |
|---|---|
| PDF | `application/pdf` |
| DOCX | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| Plain text | `text/plain` |

| Chunking Strategy | Description |
|---|---|
| `fixed` | Fixed character window with configurable overlap |
| `sentence_window` | Sliding window over NLTK sentences |
| `recursive` | Recursive split by `\n\n` → `\n` → `.` → ` ` |

---

## Key Features

- **Content-addressed deduplication** — SHA-256 of raw bytes; re-uploading the same file returns the existing record instantly
- **Byte-level MIME detection** — rejects misnamed files before any processing occurs
- **Three chunking strategies** — fixed, sentence-window, and recursive; re-chunking replaces existing chunks, never appends
- **Local embeddings** — `all-MiniLM-L6-v2` via `sentence-transformers`; 384-dim vectors stored in pgvector
- **Pluggable extractors** — add new formats by implementing `TextExtractor` in [app/extractors/](app/extractors/)
- **Integration-tested** — all tests hit a real Postgres instance (`docworkflow_test`); no mocks
- **20 MB upload limit** by default, configurable via `MAX_UPLOAD_BYTES`

---

## Getting Started

### Prerequisites

- Python ≥ 3.11
- PostgreSQL running locally with the `pgvector` extension available, and two databases:
  ```sql
  CREATE DATABASE docworkflow;
  CREATE DATABASE docworkflow_test;
  -- Run once in each database:
  CREATE EXTENSION IF NOT EXISTS vector;
  ```

### Installation

```bash
# Clone and enter the repo
git clone <repo-url>
cd polyglot-document-workflow

# Create and activate the virtual environment
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# Configure environment
cp .env.example .env
# Edit .env — set DATABASE_URL to your Postgres credentials
```

### Apply Migrations

```bash
alembic upgrade head
```

### Run the Server

```bash
uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

---

## Usage

### Ingest a document

```bash
curl -X POST http://localhost:8000/documents/ingest \
  -F "file=@/path/to/your/document.pdf"
```

**Response — new document:**
```json
{
  "doc_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "filename": "document.pdf",
  "mime_type": "application/pdf",
  "status": "ready",
  "content_hash": "e3b0c44298fc1c149afb...",
  "char_count": 4821,
  "created_at": "2026-05-16T10:00:00Z",
  "message": "Document ingested successfully."
}
```

**Response — duplicate:**
```json
{
  "status": "duplicate",
  "message": "Document already exists. Returning existing record."
}
```

### Chunk and embed a document

```bash
curl -X POST http://localhost:8000/documents/<doc_id>/chunks \
  -H "Content-Type: application/json" \
  -d '{"strategy": "fixed", "embedding_dimensions": 384, "chunk_size": 1000, "overlap": 100}'
```

**Response:**
```json
{
  "doc_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "chunk_count": 12,
  "strategy": "fixed",
  "embedding_dimensions": 384,
  "message": "Document chunked and embedded successfully."
}
```

Calling the endpoint again on the same document **replaces** existing chunks — it does not append.

### Health check

```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

---

## Running Tests

Tests require the `docworkflow_test` Postgres database to exist and be reachable.

```bash
source .venv/bin/activate
pytest
```

Each test runs in a rolled-back transaction — no state bleeds between tests.

---

## Configuration

All settings are read from `.env`. See [.env.example](.env.example) for required variables:

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | *(required)* | PostgreSQL connection string (`postgresql+psycopg://...`) |
| `MAX_UPLOAD_BYTES` | `20971520` (20 MB) | Maximum accepted file size |
| `EXTRACTED_TEXT_DIR` | `/tmp/extracted_texts` | Directory for extracted text files |

---

## Project Structure

```
app/
├── routers/
│   ├── ingest.py           # POST /documents/ingest — ingestion pipeline
│   └── chunks.py           # POST /documents/{id}/chunks — chunking + embedding
├── services/
│   └── chunking_service.py # Orchestrates chunker → embedder → repository
├── chunkers/               # Chunking strategies (fixed, sentence_window, recursive)
├── embeddings/             # Embedding provider (local sentence-transformers)
├── extractors/             # One extractor per MIME type
├── models/                 # SQLAlchemy ORM models (Document, Chunk)
├── repositories/           # DB query layer (DocumentRepository, ChunkRepository)
├── schemas/                # Pydantic request/response schemas
└── config.py               # Settings (pydantic-settings)
alembic/versions/           # Migration history
tests/
├── conftest.py             # Test DB setup and shared fixtures
├── test_ingest.py          # Phase 1 integration tests
├── test_chunkers.py        # Phase 2 chunker unit tests (no DB)
└── test_chunking_endpoint.py  # Phase 2 endpoint integration tests
```

---

## Adding a New Extractor

1. Create `app/extractors/<format>.py` implementing the `TextExtractor` protocol:
   ```python
   class MyFormatExtractor:
       def extract(self, data: bytes) -> str:
           ...
   ```
2. Register the MIME type in `app/extractors/__init__.py`
3. Add the MIME type to `allowed_mime_types` in `app/config.py`
4. Add an integration test in `tests/`

> **Note:** Check with the team before adding extractors — extraction strategy may have constraints not visible in code.

---

## Getting Help

- **API docs** — `http://localhost:8000/docs` (Swagger UI) or `/redoc`
- **Issues** — open a GitHub issue on this repository

---

## Maintainer

**Nazgul Sagatova** — [naziko6a.89@gmail.com](mailto:naziko6a.89@gmail.com)

Contributions are welcome. Open an issue first to discuss significant changes.
