"""create_day5_normalization_foundation

Revision ID: 9c2d7e4f1a05
Revises: 4b7c2d9a1f03
Create Date: 2026-09-16 12:00:00.000000+00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "9c2d7e4f1a05"
down_revision = "4b7c2d9a1f03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "normalization_runs",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("normalization_version", sa.String(length=80), nullable=False),
        sa.Column("rule_set_version", sa.String(length=80), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("records_processed", sa.Integer(), server_default="0", nullable=False),
        sa.Column("canonical_objects_created", sa.Integer(), server_default="0", nullable=False),
        sa.Column("records_matched", sa.Integer(), server_default="0", nullable=False),
        sa.Column("links_created", sa.Integer(), server_default="0", nullable=False),
        sa.Column("relationships_resolved", sa.Integer(), server_default="0", nullable=False),
        sa.Column("ambiguous_records", sa.Integer(), server_default="0", nullable=False),
        sa.Column("unresolved_records", sa.Integer(), server_default="0", nullable=False),
        sa.Column("conflicts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("warnings", sa.Integer(), server_default="0", nullable=False),
        sa.Column("errors", sa.Integer(), server_default="0", nullable=False),
        sa.Column("provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.CheckConstraint("status in ('RUNNING','COMPLETED','COMPLETED_WITH_WARNINGS','FAILED')", name="normalization_run_status_allowed"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name=op.f("fk_normalization_runs_tenant_id_tenants")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_normalization_runs")),
    )
    op.create_index("ix_normalization_runs_tenant_started", "normalization_runs", ["tenant_id", "started_at"])

    op.create_table(
        "identity_rules",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("rule_id", sa.String(length=120), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("version", sa.String(length=40), nullable=False),
        sa.Column("precedence", sa.Integer(), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column("match_conditions", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("ambiguity_behavior", sa.Text(), nullable=False),
        sa.Column("active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_identity_rules")),
        sa.UniqueConstraint("rule_id", "version", name="uq_identity_rules_rule_version"),
    )
    op.create_index("ix_identity_rules_entity_precedence", "identity_rules", ["entity_type", "precedence"])

    op.create_table(
        "source_canonical_links",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("normalization_run_id", sa.UUID(), nullable=False),
        sa.Column("staged_source_record_id", sa.UUID(), nullable=False),
        sa.Column("canonical_entity_type", sa.String(length=80), nullable=False),
        sa.Column("canonical_entity_id", sa.UUID(), nullable=True),
        sa.Column("canonical_business_identifier", sa.String(length=255), nullable=True),
        sa.Column("source_value", sa.Text(), nullable=True),
        sa.Column("normalized_value", sa.Text(), nullable=True),
        sa.Column("resolution_method", sa.String(length=80), nullable=False),
        sa.Column("resolution_rule", sa.String(length=120), nullable=False),
        sa.Column("resolution_status", sa.String(length=40), nullable=False),
        sa.Column("confidence_category", sa.String(length=40), nullable=False),
        sa.Column("human_review_status", sa.String(length=40), server_default="not_required", nullable=False),
        sa.Column("evidence_context", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("resolution_status in ('MATCHED','NEW_CANONICAL_OBJECT','AMBIGUOUS','UNRESOLVED','CONFLICT','REQUIRES_HUMAN_REVIEW')", name="source_canonical_link_status_allowed"),
        sa.CheckConstraint("confidence_category in ('DETERMINISTIC','AMBIGUOUS','UNRESOLVED','CONFLICT')", name="source_canonical_link_confidence_allowed"),
        sa.ForeignKeyConstraint(["normalization_run_id"], ["normalization_runs.id"], name=op.f("fk_source_canonical_links_normalization_run_id_normalization_runs")),
        sa.ForeignKeyConstraint(["staged_source_record_id"], ["staged_source_records.id"], name=op.f("fk_source_canonical_links_staged_source_record_id_staged_source_records")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name=op.f("fk_source_canonical_links_tenant_id_tenants")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_source_canonical_links")),
        sa.UniqueConstraint("tenant_id", "staged_source_record_id", "canonical_entity_type", "resolution_rule", name="uq_source_canonical_link_identity"),
    )
    op.create_index("ix_source_canonical_links_entity", "source_canonical_links", ["tenant_id", "canonical_entity_type", "canonical_entity_id"])
    op.create_index("ix_source_canonical_links_status", "source_canonical_links", ["tenant_id", "resolution_status"])

    op.create_table(
        "canonical_relationships",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("normalization_run_id", sa.UUID(), nullable=False),
        sa.Column("source_link_id", sa.UUID(), nullable=True),
        sa.Column("source_entity_type", sa.String(length=80), nullable=False),
        sa.Column("source_entity_id", sa.UUID(), nullable=False),
        sa.Column("target_entity_type", sa.String(length=80), nullable=False),
        sa.Column("target_entity_id", sa.UUID(), nullable=False),
        sa.Column("relationship_type", sa.String(length=120), nullable=False),
        sa.Column("resolution_rule", sa.String(length=120), nullable=False),
        sa.Column("assertion_status", sa.String(length=40), nullable=False),
        sa.Column("effective_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recorded_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("assertion_status in ('supported','contradicted','hypothesized','unknown')", name="canonical_relationship_assertion_allowed"),
        sa.ForeignKeyConstraint(["normalization_run_id"], ["normalization_runs.id"], name=op.f("fk_canonical_relationships_normalization_run_id_normalization_runs")),
        sa.ForeignKeyConstraint(["source_link_id"], ["source_canonical_links.id"], name=op.f("fk_canonical_relationships_source_link_id_source_canonical_links")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name=op.f("fk_canonical_relationships_tenant_id_tenants")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_canonical_relationships")),
        sa.UniqueConstraint("tenant_id", "source_entity_type", "source_entity_id", "target_entity_type", "target_entity_id", "relationship_type", name="uq_canonical_relationship_identity"),
    )
    op.create_index("ix_canonical_relationships_lookup", "canonical_relationships", ["tenant_id", "source_entity_type", "source_entity_id"])

    op.create_table(
        "normalization_issues",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("normalization_run_id", sa.UUID(), nullable=False),
        sa.Column("staged_source_record_id", sa.UUID(), nullable=True),
        sa.Column("issue_code", sa.String(length=80), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("severity in ('INFO','WARNING','ERROR')", name="normalization_issue_severity_allowed"),
        sa.ForeignKeyConstraint(["normalization_run_id"], ["normalization_runs.id"], name=op.f("fk_normalization_issues_normalization_run_id_normalization_runs")),
        sa.ForeignKeyConstraint(["staged_source_record_id"], ["staged_source_records.id"], name=op.f("fk_normalization_issues_staged_source_record_id_staged_source_records")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name=op.f("fk_normalization_issues_tenant_id_tenants")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_normalization_issues")),
    )
    op.create_index("ix_normalization_issues_run", "normalization_issues", ["normalization_run_id"])


def downgrade() -> None:
    op.drop_index("ix_normalization_issues_run", table_name="normalization_issues")
    op.drop_table("normalization_issues")
    op.drop_index("ix_canonical_relationships_lookup", table_name="canonical_relationships")
    op.drop_table("canonical_relationships")
    op.drop_index("ix_source_canonical_links_status", table_name="source_canonical_links")
    op.drop_index("ix_source_canonical_links_entity", table_name="source_canonical_links")
    op.drop_table("source_canonical_links")
    op.drop_index("ix_identity_rules_entity_precedence", table_name="identity_rules")
    op.drop_table("identity_rules")
    op.drop_index("ix_normalization_runs_tenant_started", table_name="normalization_runs")
    op.drop_table("normalization_runs")
