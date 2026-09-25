"""Add audit evidence metadata, password lifecycle, and compliance fields."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "ac45compliancecontrols"
down_revision = "ab44dbhardening"
branch_labels = None
depends_on = None

def upgrade():
    for name, typ in (
        ("source_ip", sa.String(64)), ("user_agent", sa.String(512)),
        ("reason", sa.Text()), ("old_values", postgresql.JSONB()),
        ("new_values", postgresql.JSONB()),
        ("retention_until", sa.DateTime(timezone=True)),
    ):
        op.add_column("audit_events", sa.Column(name, typ, nullable=True))
    op.add_column("auth_users", sa.Column("mfa_required", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("auth_users", sa.Column("mfa_enrolled_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("auth_users", sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("auth_users", sa.Column("password_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.create_table(
        "password_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_password_history_user", "password_history", ["tenant_id", "user_id", "created_at"])
    op.create_index("ix_audit_events_tenant_created", "audit_events", ["tenant_id", "created_at"])

def downgrade():
    op.drop_index("ix_audit_events_tenant_created", table_name="audit_events")
    op.drop_index("ix_password_history_user", table_name="password_history")
    op.drop_table("password_history")
    for name in ("password_expires_at", "password_changed_at", "mfa_enrolled_at", "mfa_required"):
        op.drop_column("auth_users", name)
    for name in ("retention_until", "new_values", "old_values", "reason", "user_agent", "source_ip"):
        op.drop_column("audit_events", name)
