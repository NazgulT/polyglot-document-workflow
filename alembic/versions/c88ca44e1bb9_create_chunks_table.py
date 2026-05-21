"""create chunks table

Revision ID: c88ca44e1bb9
Revises: 0001
Create Date: 2026-05-17 00:13:50.646497

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision: str = 'c88ca44e1bb9'
down_revision: Union[str, Sequence[str], None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ── Create the chunks table (was missing from original migration) ──
    op.create_table(
        "chunks",
        sa.Column("chunk_id",    UUID(as_uuid=True), primary_key=True),
        sa.Column("doc_id",      UUID(as_uuid=True),
                  sa.ForeignKey("documents.doc_id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("text",        sa.Text(),    nullable=False),
        sa.Column("char_offset", sa.Integer(), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=True),
    )

    # ── Fix documents index (idempotent — may have partially applied before) ──
    op.execute("ALTER TABLE documents DROP CONSTRAINT IF EXISTS documents_content_hash_key")
    op.execute("DROP INDEX IF EXISTS ix_documents_content_hash")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_documents_content_hash ON documents (content_hash)")

    # ── Add pgvector column and HNSW index ────────────────────────────
    op.execute("ALTER TABLE chunks ADD COLUMN IF NOT EXISTS embedding vector(384)")
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_chunks_embedding_hnsw
        ON chunks
        USING hnsw (embedding vector_cosine_ops)
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_chunks_embedding_hnsw'), table_name='chunks')
    op.drop_table("chunks")

    op.drop_index(op.f('ix_documents_content_hash'), table_name='documents')
    op.create_index(op.f('ix_documents_content_hash'), 'documents', ['content_hash'], unique=False)
    op.create_unique_constraint(op.f('documents_content_hash_key'), 'documents', ['content_hash'], postgresql_nulls_not_distinct=False)
