"""persist mapping version impact comparisons"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "x40mappingimpact"
down_revision = "w39inboundmapping"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("mapping_impact_history", sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False), sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("master_mapping_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("from_version", sa.String(40)), sa.Column("to_version", sa.String(40), nullable=False), sa.Column("impact", postgresql.JSONB(), server_default="{}", nullable=False), sa.Column("created_at", sa.DateTime(timezone=True)), sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]), sa.ForeignKeyConstraint(["master_mapping_id"], ["master_mappings.id"]), sa.PrimaryKeyConstraint("id"))

def downgrade():
    op.drop_table("mapping_impact_history")
