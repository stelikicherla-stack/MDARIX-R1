"""Durable supplier evidence requests and attachment metadata."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision = "u37stage3"; down_revision = "t36stage3"; branch_labels = None; depends_on = None
def _table(name, extra):
    op.create_table(name, sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True), sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False), *extra, sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
def upgrade():
    _table("supplier_evidence_requests", [sa.Column("investigation_id", postgresql.UUID(as_uuid=True)),sa.Column("supplier_id", postgresql.UUID(as_uuid=True)),sa.Column("requested_by", sa.String(255), nullable=False),sa.Column("recipient", sa.String(254), nullable=False),sa.Column("title", sa.String(240), nullable=False),sa.Column("requested_items", postgresql.JSONB(), nullable=False),sa.Column("status", sa.String(40), nullable=False, server_default="PENDING_DELIVERY"),sa.Column("provider_message_id", sa.String(255)),sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False)])
    _table("evidence_attachments", [sa.Column("request_id", postgresql.UUID(as_uuid=True)),sa.Column("uploaded_by", sa.String(255), nullable=False),sa.Column("filename", sa.String(255), nullable=False),sa.Column("content_type", sa.String(120), nullable=False),sa.Column("object_key", sa.String(500), nullable=False),sa.Column("size", sa.Integer(), nullable=False),sa.Column("checksum", sa.String(64), nullable=False)])
def downgrade():
    op.drop_table("evidence_attachments"); op.drop_table("supplier_evidence_requests")
