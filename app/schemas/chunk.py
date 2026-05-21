# app/schemas/chunk.py

import uuid
from pydantic import BaseModel, Field
from typing import Literal


class ChunkingConfig(BaseModel):
    strategy: Literal["fixed", "sentence_window", "recursive"]
    chunk_size: int       # characters for fixed/recursive, sentences for window
    chunk_overlap: int    # how much adjacent chunks share


class DocumentChunk(BaseModel):
    doc_id: uuid.UUID
    text: str
    char_offset: int        # character position in the original extracted text
    token_count: int        # tiktoken count — critical for LLM context window management
    # --- fields the service fills in after chunking ---
    chunk_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    chunk_index: int = 0          # service overwrites with true enumeration index
    embedding: list[float] | None = None   # None until embedding phase