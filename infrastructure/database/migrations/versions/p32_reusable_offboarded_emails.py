"""Allow recreation of an offboarded account email."""
from alembic import op

revision = "p32reusableoffboardedemails"
down_revision = "o31auditimmutability"
branch_labels = None
depends_on = None

def upgrade():
    op.drop_constraint("uq_auth_users_tenant_username", "auth_users", type_="unique")

def downgrade():
    op.create_unique_constraint("uq_auth_users_tenant_username", "auth_users", ["tenant_id", "username"])
