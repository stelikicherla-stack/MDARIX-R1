"""add master mappings and tenant mapping versions"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "n30mastermappings"
down_revision = "m29configurations"
branch_labels = None
depends_on = None

def upgrade():
    u = postgresql.UUID(as_uuid=True)
    op.create_table("master_mappings", sa.Column("id", u, server_default=sa.text("gen_random_uuid()"), nullable=False), sa.Column("code", sa.String(100), nullable=False), sa.Column("source_system", sa.String(120), nullable=False), sa.Column("target_entity", sa.String(120), nullable=False), sa.Column("definition", postgresql.JSONB(), server_default="{}", nullable=False), sa.Column("status", sa.String(30), server_default="ACTIVE", nullable=False), sa.Column("created_at", sa.DateTime(timezone=True)), sa.Column("updated_at", sa.DateTime(timezone=True)), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("code"))
    op.create_table("tenant_mapping_versions", sa.Column("id", u, server_default=sa.text("gen_random_uuid()"), nullable=False), sa.Column("tenant_id", u, nullable=False), sa.Column("master_mapping_id", u, nullable=False), sa.Column("version", sa.String(40), nullable=False), sa.Column("rules", postgresql.JSONB(), server_default="{}", nullable=False), sa.Column("status", sa.String(30), server_default="DRAFT", nullable=False), sa.Column("effective_from", sa.DateTime(timezone=True)), sa.Column("effective_to", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True)), sa.Column("updated_at", sa.DateTime(timezone=True)), sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]), sa.ForeignKeyConstraint(["master_mapping_id"], ["master_mappings.id"]), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("tenant_id", "master_mapping_id", "version", name="uq_tenant_mapping_version"), sa.UniqueConstraint("tenant_id", "id", name="uq_tenant_mapping_version_tenant_id"))
    op.create_table("tenant_mapping_overrides", sa.Column("id", u, server_default=sa.text("gen_random_uuid()"), nullable=False), sa.Column("tenant_id", u, nullable=False), sa.Column("mapping_version_id", u, nullable=False), sa.Column("field_name", sa.String(160), nullable=False), sa.Column("override_rule", postgresql.JSONB(), server_default="{}", nullable=False), sa.Column("status", sa.String(30), server_default="ACTIVE", nullable=False), sa.Column("created_at", sa.DateTime(timezone=True)), sa.Column("updated_at", sa.DateTime(timezone=True)), sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]), sa.ForeignKeyConstraint(["tenant_id", "mapping_version_id"], ["tenant_mapping_versions.tenant_id", "tenant_mapping_versions.id"]), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("tenant_id", "mapping_version_id", "field_name", name="uq_tenant_mapping_override"))

def downgrade():
    op.drop_table("tenant_mapping_overrides"); op.drop_table("tenant_mapping_versions"); op.drop_table("master_mappings")
