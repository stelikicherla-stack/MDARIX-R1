"""create versioned investigation briefs"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "d17b1e4c8a01"
down_revision = "c15d0e7a2b01"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "investigation_briefs",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("investigation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True)),
        sa.Column("product_version_id", postgresql.UUID(as_uuid=True)),
        sa.Column("brief_version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(40), server_default="GENERATED", nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("generated_by", sa.String(255), nullable=False),
        sa.Column("temporal_mode", sa.String(20), nullable=False),
        sa.Column("temporal_cutoff", sa.DateTime(timezone=True)),
        sa.Column("ai_execution_id", postgresql.UUID(as_uuid=True)),
        sa.Column("human_review_state", sa.String(40), server_default="NOT_REVIEWED", nullable=False),
        sa.Column("decision_id", postgresql.UUID(as_uuid=True)),
        sa.Column("limitations", postgresql.JSONB()),
        sa.Column("content", postgresql.JSONB(), nullable=False),
        sa.Column("provenance", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["tenant_id", "investigation_id"], ["investigations.tenant_id", "investigations.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "investigation_id", "brief_version", name="uq_briefs_tenant_investigation_version"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_briefs_tenant_id_id"),
    )

def downgrade() -> None:
    op.drop_table("investigation_briefs")
