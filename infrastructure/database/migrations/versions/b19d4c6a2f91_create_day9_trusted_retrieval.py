"""create_day9_trusted_retrieval

Revision ID: b19d4c6a2f91
Revises: 8a3f1d7e2b08
Create Date: 2026-09-16 18:30:00.000000+00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "b19d4c6a2f91"
down_revision = "8a3f1d7e2b08"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "evidence_chunk_embeddings",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("evidence_id", sa.UUID(), nullable=False),
        sa.Column("chunk_id", sa.UUID(), nullable=False),
        sa.Column("chunk_checksum", sa.String(length=128), nullable=False),
        sa.Column("provider", sa.String(length=120), nullable=False),
        sa.Column("embedding_model", sa.String(length=120), nullable=False),
        sa.Column("model_version", sa.String(length=120), nullable=False),
        sa.Column("embedding_dimension", sa.Integer(), nullable=False),
        sa.Column("pipeline_version", sa.String(length=120), nullable=False),
        sa.Column("distance_metric", sa.String(length=40), server_default="cosine", nullable=False),
        sa.Column("embedding", sa.String(), nullable=True),
        sa.Column("indexing_status", sa.String(length=40), server_default="INDEXED", nullable=False),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("indexing_status in ('INDEXED','FAILED')", name="chunk_embedding_status_allowed"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name=op.f("fk_evidence_chunk_embeddings_tenant_id_tenants")),
        sa.ForeignKeyConstraint(
            ["tenant_id", "evidence_id"],
            ["evidence.tenant_id", "evidence.id"],
            name="fk_chunk_embeddings_tenant_id_evidence_id",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "chunk_id"],
            ["evidence_chunks.tenant_id", "evidence_chunks.id"],
            name="fk_chunk_embeddings_tenant_id_chunk_id",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_evidence_chunk_embeddings")),
        sa.UniqueConstraint(
            "tenant_id",
            "chunk_id",
            "chunk_checksum",
            "embedding_model",
            "model_version",
            "pipeline_version",
            name="uq_evidence_chunk_embedding_version",
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_evidence_chunk_embeddings_tenant_id_id"),
    )
    op.execute("ALTER TABLE evidence_chunk_embeddings ALTER COLUMN embedding TYPE vector(32) USING embedding::vector")
    op.create_index(
        "ix_chunk_embeddings_tenant_chunk",
        "evidence_chunk_embeddings",
        ["tenant_id", "chunk_id"],
        unique=False,
    )
    op.create_index(
        "ix_chunk_embeddings_tenant_status",
        "evidence_chunk_embeddings",
        ["tenant_id", "indexing_status"],
        unique=False,
    )
    op.execute(
        "CREATE INDEX ix_chunk_embeddings_embedding_hnsw "
        "ON evidence_chunk_embeddings USING hnsw (embedding vector_cosine_ops) "
        "WHERE indexing_status = 'INDEXED'"
    )

    op.create_table(
        "retrieval_queries",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("investigation_id", sa.UUID(), nullable=True),
        sa.Column("query_text", sa.Text(), nullable=False),
        sa.Column("retrieval_mode", sa.String(length=40), nullable=False),
        sa.Column("temporal_mode", sa.String(length=40), server_default="current", nullable=False),
        sa.Column("filters", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("embedding_model", sa.String(length=120), nullable=True),
        sa.Column("embedding_model_version", sa.String(length=120), nullable=True),
        sa.Column("retrieval_config_version", sa.String(length=120), nullable=False),
        sa.Column("top_k", sa.Integer(), nullable=False),
        sa.Column("returned_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint("retrieval_mode in ('structured','semantic','hybrid')", name="retrieval_mode_allowed"),
        sa.CheckConstraint("temporal_mode in ('current','event','known')", name="retrieval_temporal_mode_allowed"),
        sa.CheckConstraint(
            "status in ('COMPLETED','NO_RELEVANT_EVIDENCE','INSUFFICIENT_RELEVANT_EVIDENCE','FAILED')",
            name="retrieval_status_allowed",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name=op.f("fk_retrieval_queries_tenant_id_tenants")),
        sa.ForeignKeyConstraint(
            ["tenant_id", "investigation_id"],
            ["investigations.tenant_id", "investigations.id"],
            name="fk_retrieval_queries_tenant_id_investigation_id",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_retrieval_queries")),
        sa.UniqueConstraint("tenant_id", "id", name="uq_retrieval_queries_tenant_id_id"),
    )
    op.create_index("ix_retrieval_queries_tenant_created", "retrieval_queries", ["tenant_id", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_retrieval_queries_tenant_created", table_name="retrieval_queries")
    op.drop_table("retrieval_queries")
    op.execute("DROP INDEX IF EXISTS ix_chunk_embeddings_embedding_hnsw")
    op.drop_index("ix_chunk_embeddings_tenant_status", table_name="evidence_chunk_embeddings")
    op.drop_index("ix_chunk_embeddings_tenant_chunk", table_name="evidence_chunk_embeddings")
    op.drop_table("evidence_chunk_embeddings")
