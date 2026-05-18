from functools import lru_cache


@lru_cache
def get_default_provider():
    # Deferred so the heavy sentence_transformers / torch stack is only
    # loaded when the first embedding request arrives, not at import time.
    from app.embeddings.local import LocalSentenceTransformerProvider
    return LocalSentenceTransformerProvider()
