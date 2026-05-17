# tests/conftest.py

import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import create_app
from app.database import get_db
from app.models.document import Base
from app.config import get_settings, Settings


# ── Override settings for tests ──────────────────────────────────────────────

TEST_DATABASE_URL = "postgresql+psycopg://Nazgul@localhost:5432/docworkflow_test"


def get_test_settings() -> Settings:
    return Settings(
        database_url=TEST_DATABASE_URL,
        extracted_text_dir="/tmp/test_extracted",
    )


# ── Test DB engine ────────────────────────────────────────────────────────────

test_engine = create_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.rollback()    # Roll back each test — no state bleeds between tests
        session.close()


@pytest.fixture
def client(db_session):
    app = create_app()

    def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_settings] = get_test_settings

    with TestClient(app) as c:
        yield c


# ── File fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture
def sample_txt_bytes() -> bytes:
    return b"This is a plain text document used for testing the ingestion pipeline."


@pytest.fixture
def sample_txt_file(sample_txt_bytes):
    return ("file", ("test.txt", io.BytesIO(sample_txt_bytes), "text/plain"))