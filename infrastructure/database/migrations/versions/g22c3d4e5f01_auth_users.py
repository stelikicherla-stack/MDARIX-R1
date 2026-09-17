"""add persisted authentication users"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision="g22c3d4e5f01"; down_revision="f19b2c3d4e01"; branch_labels=None; depends_on=None
def upgrade():
 u=postgresql.UUID(as_uuid=True); op.create_table("auth_users",sa.Column("id",u,server_default=sa.text("gen_random_uuid()"),nullable=False),sa.Column("tenant_id",u,nullable=False),sa.Column("username",sa.String(254),nullable=False),sa.Column("display_name",sa.String(120),nullable=False),sa.Column("company",sa.String(160),nullable=False),sa.Column("password_hash",sa.Text(),nullable=False),sa.Column("role",sa.String(120),server_default="Viewer",nullable=False),sa.Column("status",sa.String(40),server_default="PENDING_VERIFICATION",nullable=False),sa.Column("email_verified",sa.Boolean(),server_default="false",nullable=False),sa.Column("created_at",sa.DateTime(timezone=True)),sa.Column("updated_at",sa.DateTime(timezone=True)),sa.PrimaryKeyConstraint("id"),sa.UniqueConstraint("tenant_id","username",name="uq_auth_users_tenant_username"),sa.UniqueConstraint("tenant_id","id",name="uq_auth_users_tenant_id_id"))
def downgrade(): op.drop_table("auth_users")
