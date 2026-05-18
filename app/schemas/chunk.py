# app/schemas/chunk.py

import uuid
from pydantic import BaseModel
from typing import Literal

class ChunkingConfig(BaseModel):
    strategy: Literal["fixed", "sentence_window", "recursive"]
    chunk_size: int       # characters for fixed/recursive, sentences for window
    chunk_overlap: int    # how much adjacent chunks share

class DocumentChunk(BaseModel):
    chunk_id: uuid.UUID
    doc_id: uuid.UUID
    chunk_index: int        # 0-based position within the document
    text: str
    char_offset: int        # character position in the original extracted text
    token_count: int        # tiktoken count — critical for LLM context window management
    embedding: list[float] | None   # None until embedding phase runs