"""create_day8_evidence_intelligence

Revision ID: 8a3f1d7e2b08
Revises: 9c2d7e4f1a05
Create Date: 2026-09-16 16:00:00.000000+00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "8a3f1d7e2b08"
down_revision = "9c2d7e4f1a05"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "evidence_chunks",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("evidence_id", sa.UUID(), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("text_content", sa.Text(), nullable=False),
        sa.Column("source_anchor", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("checksum", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name=op.f("fk_evidence_chunks_tenant_id_tenants")),
        sa.ForeignKeyConstraint(
            ["tenant_id", "evidence_id"],
            ["evidence.tenant_id", "evidence.id"],
            name="fk_evidence_chunks_tenant_id_evidence_id",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_evidence_chunks")),
        sa.UniqueConstraint("tenant_id", "evidence_id", "sequence_number", name="uq_evidence_chunks_sequence"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_evidence_chunks_tenant_id_id"),
    )
    op.create_index(
        "ix_evidence_chunks_tenant_evidence",
        "evidence_chunks",
        ["tenant_id", "evidence_id"],
        unique=False,
    )

    op.create_table(
        "evidence_observations",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("evidence_id", sa.UUID(), nullable=False),
        sa.Column("chunk_id", sa.UUID(), nullable=True),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("observation_type", sa.String(length=80), server_default="AI_EXTRACTED_OBSERVATION", nullable=False),
        sa.Column("extraction_method", sa.String(length=40), server_default="DETERMINISTIC", nullable=False),
        sa.Column("source_anchor", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("effective_context", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("quality_status", sa.String(length=40), server_default="VALIDATED", nullable=False),
        sa.Column("limitations", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ai_execution_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint(
            "observation_type in ('EXPLICIT_SOURCE_STATEMENT','STRUCTURED_EXTRACTION','DETERMINISTIC_DERIVATION','AI_EXTRACTED_OBSERVATION')",
            name="evidence_obs_type_allowed",
        ),
        sa.CheckConstraint(
            "extraction_method in ('DETERMINISTIC','GENAI')",
            name="evidence_obs_method_allowed",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name=op.f("fk_evidence_observations_tenant_id_tenants")),
        sa.ForeignKeyConstraint(
            ["tenant_id", "evidence_id"],
            ["evidence.tenant_id", "evidence.id"],
            name="fk_evidence_observations_tenant_id_evidence_id",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "chunk_id"],
            ["evidence_chunks.tenant_id", "evidence_chunks.id"],
            name="fk_evidence_observations_tenant_id_chunk_id",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "ai_execution_id"],
            ["ai_executions.tenant_id", "ai_executions.id"],
            name="fk_evidence_observations_tenant_id_ai_execution_id",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_evidence_observations")),
        sa.UniqueConstraint("tenant_id", "id", name="uq_evidence_observations_tenant_id_id"),
    )
    op.create_index(
        "ix_evidence_observations_tenant_evidence",
        "evidence_observations",
        ["tenant_id", "evidence_id"],
        unique=False,
    )

    op.create_table(
        "evidence_entity_links",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("evidence_id", sa.UUID(), nullable=False),
        sa.Column("observation_id", sa.UUID(), nullable=True),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.UUID(), nullable=True),
        sa.Column("raw_reference", sa.Text(), nullable=True),
        sa.Column("resolution_status", sa.String(length=40), server_default="RESOLVED", nullable=False),
        sa.Column("confidence_score", sa.String(length=40), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint(
            "resolution_status in ('RESOLVED','UNRESOLVED')",
            name="evidence_entity_link_status_allowed",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name=op.f("fk_evidence_entity_links_tenant_id_tenants")),
        sa.ForeignKeyConstraint(
            ["tenant_id", "evidence_id"],
            ["evidence.tenant_id", "evidence.id"],
            name="fk_evidence_entity_links_tenant_id_evidence_id",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "observation_id"],
            ["evidence_observations.tenant_id", "evidence_observations.id"],
            name="fk_evidence_entity_links_tenant_id_obs_id",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_evidence_entity_links")),
        sa.UniqueConstraint("tenant_id", "id", name="uq_evidence_entity_links_tenant_id_id"),
    )
    op.create_index(
        "ix_evidence_entity_links_tenant_evidence",
        "evidence_entity_links",
        ["tenant_id", "evidence_id"],
        unique=False,
    )

    op.create_table(
        "evidence_proposition_relations",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("observation_id", sa.UUID(), nullable=False),
        sa.Column("proposition_text", sa.Text(), nullable=False),
        sa.Column("relation_type", sa.String(length=40), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint(
            "relation_type in ('SUPPORT','CONTRADICT','NEUTRAL_CONTEXTUAL')",
            name="evidence_prop_relation_type_allowed",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name=op.f("fk_evidence_proposition_relations_tenant_id_tenants")),
        sa.ForeignKeyConstraint(
            ["tenant_id", "observation_id"],
            ["evidence_observations.tenant_id", "evidence_observations.id"],
            name="fk_evidence_prop_relations_tenant_id_obs_id",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_evidence_proposition_relations")),
        sa.UniqueConstraint("tenant_id", "id", name="uq_evidence_proposition_relations_tenant_id_id"),
    )


def downgrade() -> None:
    op.drop_table("evidence_proposition_relations")
    op.drop_table("evidence_entity_links")
    op.drop_table("evidence_observations")
    op.drop_table("evidence_chunks")
