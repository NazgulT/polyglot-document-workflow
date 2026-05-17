# Polyglot Document Workflow

A document ingestion pipeline built with **FastAPI** and **PostgreSQL** that accepts PDF, DOCX, and plain-text files, extracts their text content, and deduplicates by content hash — designed as Step 1 of a polyglot RAG (Retrieval-Augmented Generation) system.

---

## What It Does

Upload a document via HTTP and the pipeline will:

1. **Validate** file size and detect the MIME type from raw bytes (never from filename)
2. **Fingerprint** the content with SHA-256 and skip storage if the document already exists
3. **Extract** clean UTF-8 text using a format-specific extractor (PDF via PyMuPDF, DOCX via python-docx, plain text natively)
4. **Persist** the record in PostgreSQL and return a structured response with `doc_id`, `status`, and `char_count`

| Supported Format | MIME Type |
|---|---|
| PDF | `application/pdf` |
| DOCX | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| Plain text | `text/plain` |

---

## Key Features

- **Content-addressed deduplication** — SHA-256 of raw bytes; re-uploading the same file returns the existing record instantly
- **Byte-level MIME detection** — rejects misnamed files before any processing occurs
- **Pluggable extractors** — add new formats by implementing the `TextExtractor` protocol in [app/extractors/](app/extractors/)
- **Integration-tested** — tests run against a real Postgres instance (`docworkflow_test`); no mocks
- **20 MB upload limit** by default, configurable via `MAX_UPLOAD_BYTES`

---

## Getting Started

### Prerequisites

- Python ≥ 3.11
- PostgreSQL running locally with two databases:
  ```sql
  CREATE DATABASE docworkflow;
  CREATE DATABASE docworkflow_test;
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
├── routers/ingest.py       # POST /documents/ingest — full pipeline
├── extractors/             # One extractor per MIME type
│   ├── base.py             # TextExtractor protocol + ExtractionError
│   ├── pdf.py
│   ├── docx.py
│   └── plain.py
├── models/                 # SQLAlchemy ORM models
├── repositories/           # DB query layer
├── schemas/document.py     # Pydantic request/response schemas
└── config.py               # Settings (pydantic-settings)
alembic/versions/           # Migration history
tests/
├── conftest.py             # Test DB setup and fixtures
└── test_ingest.py
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
