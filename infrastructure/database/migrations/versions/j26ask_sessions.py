"""add Day 26 controlled Ask investigation sessions"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "j26asksessions"
down_revision = "i25enterprise"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("investigation_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("owner_user_id", sa.String(254), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="ACTIVE"),
        sa.Column("active_product_id", postgresql.UUID(as_uuid=True)),
        sa.Column("active_product_version_id", postgresql.UUID(as_uuid=True)),
        sa.Column("temporal_context", postgresql.JSONB()),
        sa.Column("previous_query_id", sa.String(120)),
        sa.Column("policy_provenance", postgresql.JSONB()),
        sa.Column("correlation_id", sa.String(120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("tenant_id", "id", name="uq_investigation_sessions_tenant_id_id"))

def downgrade():
    op.drop_table("investigation_sessions")
