from pydantic import BaseModel, Field
from typing import List, Optional
import uuid

class SearchFilters(BaseModel):

    """
    Optional constraints applied before vector similarity ranking.

    Filtering happens at the SQL level (WHERE clause), not post-hoc on results.
    This matters for correctness: top_k=5 with a doc_id filter returns the 5
    best chunks *within that document*, not the 5 globally best chunks filtered
    down after the fact.
    """

    doc_ids: Optional[List[uuid.UUID]] = Field(None, description="Filter by document IDs")
    min_score: Optional[float] = Field(default=0.0, ge=0.0, le=1.0, description="Filter by minimum score")

class SearchQuery(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000, description="The search query text")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of top results to return")
    filters: Optional[SearchFilters] = Field(None, description="Optional filters for the search")

class SearchResult(BaseModel):  
    doc_id: uuid.UUID = Field(..., description="The ID of the document")
    chunk_id: uuid.UUID = Field(..., description="The ID of the chunk")
    chunk_index: int = Field(..., description="The index of the chunk within the document")
    char_offset: int = Field(..., description="The character offset of the chunk in the original document")
    score: float = Field(..., description="The relevance score of the result. The cosine similarity score.")
    text: str = Field(..., description="The text of the chunk that matched the search query")
    filename: str = Field(..., description="The filename of the document that the chunk belongs to")

class SearchResponse(BaseModel):
    query: str = Field(..., description="The original search query")
    query_embedding_ms: float = Field(..., description="Time taken to compute the query embedding in milliseconds")
    result_count: int = Field(..., description="Total number of results returned")
    results: List[SearchResult] = Field(..., description="The list of search results")

class UpsertRequest(BaseModel):
    doc_id: uuid.UUID = Field(..., description="The ID of the document to upsert")

class UpsertResponse(BaseModel):
    doc_id: uuid.UUID = Field(..., description="The ID of the document that was upserted")
    success: bool = Field(..., description="Whether the upsert operation was successful")
    chunks_upserted: int = Field(..., description="The number of chunks that were upserted for this document")
    message: Optional[str] = Field(None, description="Additional information about the upsert operation")