from typing import Protocol

class EmbeddingProvider(Protocol):
    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        ...

    @property
    def dimensions(self) -> int:
        # Number of floats in each embedding vector
        # Required so the pgvector column can be sized correctly
        ...