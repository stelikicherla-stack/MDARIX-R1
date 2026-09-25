"""Add shared durable login throttling and lockout state."""
from alembic import op
import sqlalchemy as sa

revision = "aa43loginthrottles"
down_revision = "z42publiconboarding"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("login_throttles",
        sa.Column("identifier", sa.String(254), primary_key=True),
        sa.Column("failure_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("locked_until", sa.DateTime(timezone=True)),
        sa.Column("last_failure_at", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))

def downgrade():
    op.drop_table("login_throttles")
