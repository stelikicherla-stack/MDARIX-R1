"""Add tenant-scoped indexes for security and bounded list performance."""
from alembic import op

revision = "v38securityindexes"
down_revision = "u37stage3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_auth_sessions_tenant_expires", "auth_sessions", ["tenant_id", "expires_at"])
    op.create_index("ix_ai_interactions_tenant_user_created", "ai_interactions", ["tenant_id", "user_id", "created_at"])
    op.create_index("ix_supplier_requests_tenant_created", "supplier_evidence_requests", ["tenant_id", "created_at"])
    op.create_index("ix_evidence_attachments_tenant_request", "evidence_attachments", ["tenant_id", "request_id"])


def downgrade() -> None:
    op.drop_index("ix_evidence_attachments_tenant_request", table_name="evidence_attachments")
    op.drop_index("ix_supplier_requests_tenant_created", table_name="supplier_evidence_requests")
    op.drop_index("ix_ai_interactions_tenant_user_created", table_name="ai_interactions")
    op.drop_index("ix_auth_sessions_tenant_expires", table_name="auth_sessions")
