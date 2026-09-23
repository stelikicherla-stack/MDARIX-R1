"""Add durable provider-account to tenant mapping for inbound webhooks."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "w39inboundmapping"
down_revision = "v38securityindexes"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("inbound_provider_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(80), nullable=False),
        sa.Column("provider_account_id", sa.String(255), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.UniqueConstraint("provider", "provider_account_id", name="uq_inbound_provider_account"))
    op.create_index("ix_inbound_provider_mapping_tenant", "inbound_provider_mappings", ["tenant_id", "provider"])

def downgrade():
    op.drop_index("ix_inbound_provider_mapping_tenant", table_name="inbound_provider_mappings")
    op.drop_table("inbound_provider_mappings")
