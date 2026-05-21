# app/vector_store/__init__.py

from sqlalchemy.orm import Session

from .pgvector_store import VectorStore


def get_vector_store(db: Session) -> VectorStore:
    """
    FastAPI dependency factory.

    Usage in a router:
        store: VectorStore = Depends(get_vector_store_dep)

    Accepts a Session injected by get_db so the store participates
    in the same transaction as any other repository in the same request.
    """
    return VectorStore(db)