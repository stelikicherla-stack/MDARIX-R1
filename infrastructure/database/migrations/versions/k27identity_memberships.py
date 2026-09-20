"""add tenant membership and persona assignment records"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "k27identitymemberships"
down_revision = "j26asksessions"
branch_labels = None
depends_on = None


def upgrade():
    u = postgresql.UUID(as_uuid=True)
    op.create_table(
        "tenant_memberships",
        sa.Column("id", u, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", u, nullable=False),
        sa.Column("user_id", u, nullable=False),
        sa.Column("status", sa.String(30), server_default="ACTIVE", nullable=False),
        sa.Column("is_default", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["tenant_id", "user_id"], ["auth_users.tenant_id", "auth_users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "user_id", name="uq_tenant_membership"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_tenant_membership_tenant_id"),
    )
    op.create_table(
        "persona_assignments",
        sa.Column("id", u, server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", u, nullable=False),
        sa.Column("user_id", u, nullable=False),
        sa.Column("persona_code", sa.String(80), nullable=False),
        sa.Column("status", sa.String(30), server_default="ACTIVE", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["tenant_id", "user_id"], ["auth_users.tenant_id", "auth_users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "user_id", "persona_code", name="uq_persona_assignment"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_persona_assignment_tenant_id"),
    )


def downgrade():
    op.drop_table("persona_assignments")
    op.drop_table("tenant_memberships")
