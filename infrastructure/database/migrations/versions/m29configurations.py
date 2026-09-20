"""add tenant-scoped connector and mapping configurations"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "m29configurations"
down_revision = "l28rolespermissions"
branch_labels = None
depends_on = None

def upgrade():
    u = postgresql.UUID(as_uuid=True)
    for table, columns, unique in [
        ("connector_configurations", [sa.Column("code", sa.String(100), nullable=False), sa.Column("connector_type", sa.String(80), nullable=False), sa.Column("configuration", postgresql.JSONB(), server_default="{}", nullable=False)], "uq_connector_configuration"),
        ("mapping_configurations", [sa.Column("code", sa.String(100), nullable=False), sa.Column("source_system", sa.String(120), nullable=False), sa.Column("target_entity", sa.String(120), nullable=False), sa.Column("mapping_rules", postgresql.JSONB(), server_default="{}", nullable=False)], "uq_mapping_configuration"),
    ]:
        op.create_table(table, sa.Column("id", u, server_default=sa.text("gen_random_uuid()"), nullable=False), sa.Column("tenant_id", u, nullable=False), *columns, sa.Column("version", sa.String(40), server_default="v1", nullable=False), sa.Column("status", sa.String(30), server_default="DRAFT", nullable=False), sa.Column("created_at", sa.DateTime(timezone=True)), sa.Column("updated_at", sa.DateTime(timezone=True)), sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("tenant_id", "code", "version", name=unique))

def downgrade():
    op.drop_table("mapping_configurations")
    op.drop_table("connector_configurations")
