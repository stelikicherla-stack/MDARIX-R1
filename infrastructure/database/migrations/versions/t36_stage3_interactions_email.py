"""Add durable Stage 3 interaction, snapshot, and inbound email records."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision = "t36stage3"; down_revision = "s35outbox"; branch_labels = None; depends_on = None

def _common(name):
    op.create_table(name, sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True), sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))

def upgrade():
    _common("ai_interaction_sessions"); op.add_column("ai_interaction_sessions", sa.Column("user_id", sa.String(255), nullable=False)); op.add_column("ai_interaction_sessions", sa.Column("membership_id", postgresql.UUID(as_uuid=True))); op.add_column("ai_interaction_sessions", sa.Column("role_id", sa.String(120))); op.add_column("ai_interaction_sessions", sa.Column("page_context", sa.String(120))); op.add_column("ai_interaction_sessions", sa.Column("correlation_id", sa.String(120), nullable=False)); op.add_column("ai_interaction_sessions", sa.Column("status", sa.String(30), server_default="ACTIVE", nullable=False)); op.add_column("ai_interaction_sessions", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    _common("ai_interactions");
    for name, typ, nullable in [("session_id", postgresql.UUID(as_uuid=True), False),("user_id",sa.String(255),False),("product_id",postgresql.UUID(as_uuid=True),True),("product_version_id",postgresql.UUID(as_uuid=True),True),("investigation_id",postgresql.UUID(as_uuid=True),True),("user_prompt",sa.Text(),False),("normalized_intent",sa.String(120),True),("temporal_mode",sa.String(30),True),("temporal_cutoff",sa.DateTime(timezone=True),True),("response",postgresql.JSONB(),False),("provenance",postgresql.JSONB(),True),("correlation_id",sa.String(120),False)]: op.add_column("ai_interactions", sa.Column(name,typ,nullable=nullable))
    _common("ai_interaction_feedback"); op.add_column("ai_interaction_feedback", sa.Column("interaction_id",postgresql.UUID(as_uuid=True),nullable=False)); op.add_column("ai_interaction_feedback", sa.Column("user_id",sa.String(255),nullable=False)); op.add_column("ai_interaction_feedback", sa.Column("feedback",postgresql.JSONB(),nullable=False))
    _common("context_snapshots");
    for name, typ, nullable in [("decision_id",postgresql.UUID(as_uuid=True),False),("decision_version",sa.String(80),False),("snapshot",postgresql.JSONB(),False),("created_by",sa.String(255),False)]: op.add_column("context_snapshots", sa.Column(name,typ,nullable=nullable))
    _common("inbound_email_events"); op.alter_column("inbound_email_events", "tenant_id", nullable=True)
    for name, typ, nullable in [("provider_event_id",sa.String(255),False),("event_type",sa.String(100),False),("status",sa.String(50),False),("metadata",postgresql.JSONB(),True)]: op.add_column("inbound_email_events", sa.Column(name,typ,nullable=nullable))
    op.create_unique_constraint("uq_inbound_email_provider_event", "inbound_email_events", ["provider_event_id"])

def downgrade():
    for name in ("inbound_email_events","context_snapshots","ai_interaction_feedback","ai_interactions","ai_interaction_sessions"): op.drop_table(name)
