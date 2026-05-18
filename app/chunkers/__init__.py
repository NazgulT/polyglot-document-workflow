from app.chunkers.base import ChunkingStrategy
from app.chunkers.fixed import FixedSizeChunker
from app.chunkers.sentence_window import SentenceWindowChunker
from app.chunkers.recursive import RecursiveCharacterChunker
from app.schemas.chunk import ChunkingConfig

_REGISTRY: dict[str, type[ChunkingStrategy]] = {
    "fixed": FixedSizeChunker,
    "sentence_window": SentenceWindowChunker,
    "recursive": RecursiveCharacterChunker,
}

def get_chunker(config: ChunkingConfig) -> ChunkingStrategy:
    cls = _REGISTRY.get(config.strategy)
    if cls is None:
        raise ValueError(f"Unknown chunking strategy: {config.strategy}")
    if cls is SentenceWindowChunker:
        return cls(window_size=config.chunk_size)
    if cls is RecursiveCharacterChunker:
        return cls(chunk_size=config.chunk_size)
    return cls(chunk_size=config.chunk_size, chunk_overlap=config.chunk_overlap)