# app/database.py

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings


def _make_engine():
    settings = get_settings()
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,      # Detect stale connections before use
        pool_size=5,
        max_overflow=10,
        echo=False,              # Set True to log SQL in development
    )


engine = _make_engine()

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,      # Avoid lazy-load errors after commit
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency — yields a session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()