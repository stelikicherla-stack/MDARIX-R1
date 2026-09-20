"""add tenant-scoped role and permission definitions"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "l28rolespermissions"
down_revision = "k27identitymemberships"
branch_labels = None
depends_on = None


def upgrade():
    u = postgresql.UUID(as_uuid=True)
    op.create_table("permission_set_definitions",
        sa.Column("id", u, server_default=sa.text("gen_random_uuid()"), nullable=False), sa.Column("tenant_id", u, nullable=False),
        sa.Column("code", sa.String(100), nullable=False), sa.Column("object_permissions", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("field_permissions", postgresql.JSONB(), server_default="{}", nullable=False), sa.Column("action_permissions", postgresql.JSONB(), server_default="{}", nullable=False),
        sa.Column("version", sa.String(40), server_default="v1", nullable=False), sa.Column("status", sa.String(30), server_default="DRAFT", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True)), sa.Column("updated_at", sa.DateTime(timezone=True)), sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]), sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "code", "version", name="uq_permission_set_definition"), sa.UniqueConstraint("tenant_id", "id", name="uq_permission_set_definition_tenant_id"))
    op.create_table("role_definitions",
        sa.Column("id", u, server_default=sa.text("gen_random_uuid()"), nullable=False), sa.Column("tenant_id", u, nullable=False), sa.Column("code", sa.String(100), nullable=False), sa.Column("name", sa.String(120), nullable=False),
        sa.Column("version", sa.String(40), server_default="v1", nullable=False), sa.Column("status", sa.String(30), server_default="DRAFT", nullable=False), sa.Column("created_at", sa.DateTime(timezone=True)), sa.Column("updated_at", sa.DateTime(timezone=True)), sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("tenant_id", "code", "version", name="uq_role_definition"), sa.UniqueConstraint("tenant_id", "id", name="uq_role_definition_tenant_id"))
    op.create_table("role_permission_sets",
        sa.Column("id", u, server_default=sa.text("gen_random_uuid()"), nullable=False), sa.Column("tenant_id", u, nullable=False), sa.Column("role_id", u, nullable=False), sa.Column("permission_set_id", u, nullable=False), sa.Column("created_at", sa.DateTime(timezone=True)), sa.ForeignKeyConstraint(["tenant_id", "role_id"], ["role_definitions.tenant_id", "role_definitions.id"]), sa.ForeignKeyConstraint(["tenant_id", "permission_set_id"], ["permission_set_definitions.tenant_id", "permission_set_definitions.id"]), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("tenant_id", "role_id", "permission_set_id", name="uq_role_permission_set"))
    op.create_table("role_assignments",
        sa.Column("id", u, server_default=sa.text("gen_random_uuid()"), nullable=False), sa.Column("tenant_id", u, nullable=False), sa.Column("user_id", u, nullable=False), sa.Column("role_id", u, nullable=False), sa.Column("status", sa.String(30), server_default="ACTIVE", nullable=False), sa.Column("created_at", sa.DateTime(timezone=True)), sa.Column("updated_at", sa.DateTime(timezone=True)), sa.ForeignKeyConstraint(["tenant_id", "user_id"], ["auth_users.tenant_id", "auth_users.id"]), sa.ForeignKeyConstraint(["tenant_id", "role_id"], ["role_definitions.tenant_id", "role_definitions.id"]), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("tenant_id", "user_id", "role_id", name="uq_role_assignment"), sa.UniqueConstraint("tenant_id", "id", name="uq_role_assignment_tenant_id"))


def downgrade():
    op.drop_table("role_assignments")
    op.drop_table("role_permission_sets")
    op.drop_table("role_definitions")
    op.drop_table("permission_set_definitions")
