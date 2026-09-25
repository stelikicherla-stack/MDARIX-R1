"""Replace public tenant creation with pending onboarding requests."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "z42publiconboarding"
down_revision = "y41subscriptionlifecycle"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "onboarding_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("organization", sa.String(160), nullable=False),
        sa.Column("status", sa.String(40), server_default="PENDING_REVIEW", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_onboarding_requests_email"),
    )

def downgrade():
    op.drop_table("onboarding_requests")
