"""add Day 15 decision context fields"""
from alembic import op
import sqlalchemy as sa

revision = "c15d0e7a2b01"
down_revision = "b19d4c6a2f91"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("decisions", sa.Column("product_id", sa.UUID(), nullable=True))
    op.add_column("decisions", sa.Column("product_version_id", sa.UUID(), nullable=True))
    op.add_column("decisions", sa.Column("decision_status", sa.String(length=50), server_default="DRAFT", nullable=False))
    op.add_column("decisions", sa.Column("decision_readiness", sa.String(length=80), nullable=True))
    op.add_column("decisions", sa.Column("selected_action", sa.String(length=120), nullable=True))
    op.add_column("decisions", sa.Column("human_decision", sa.Text(), nullable=True))
    op.add_column("decisions", sa.Column("limitations", sa.JSON(), nullable=True))
    op.add_column("decisions", sa.Column("temporal_context", sa.JSON(), nullable=True))
    op.add_column("decisions", sa.Column("context_snapshot", sa.JSON(), nullable=True))
    op.add_column("decisions", sa.Column("advisory_execution_id", sa.UUID(), nullable=True))
    op.add_column("decisions", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    for name in ("updated_at", "advisory_execution_id", "context_snapshot", "temporal_context", "limitations", "human_decision", "selected_action", "decision_readiness", "decision_status", "product_version_id", "product_id"):
        op.drop_column("decisions", name)
