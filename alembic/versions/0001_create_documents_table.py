# alembic/versions/0001_create_documents_table.py

"""create documents table

Revision ID: 0001
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0001"
down_revision = None


def upgrade() -> None:
    # Ensure pgvector is available — safe to run even if already installed
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "documents",
        sa.Column("doc_id",         UUID(as_uuid=True), primary_key=True),
        sa.Column("filename",       sa.String(512),  nullable=False),
        sa.Column("mime_type",      sa.String(128),  nullable=False),
        sa.Column("content_hash",   sa.String(64),   nullable=False, unique=True),
        sa.Column("char_count",     sa.Integer(),    nullable=False),
        sa.Column("extracted_path", sa.Text(),       nullable=False),
        sa.Column("status",         sa.String(32),   nullable=False),
        sa.Column("created_at",     sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_documents_content_hash", "documents", ["content_hash"])


def downgrade() -> None:
    op.drop_table("documents")