"""create_day4_ingestion_foundation

Revision ID: 4b7c2d9a1f03
Revises: ea1eb54290f5
Create Date: 2026-09-16 10:30:00.000000+00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "4b7c2d9a1f03"
down_revision = "ea1eb54290f5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("source_system", sa.String(length=80), nullable=False),
        sa.Column("source_type", sa.String(length=80), nullable=False),
        sa.Column("source_file", sa.Text(), nullable=False),
        sa.Column("source_checksum", sa.String(length=64), nullable=False),
        sa.Column("ingestion_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ingestion_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("total_records", sa.Integer(), server_default="0", nullable=False),
        sa.Column("accepted_records", sa.Integer(), server_default="0", nullable=False),
        sa.Column("warning_records", sa.Integer(), server_default="0", nullable=False),
        sa.Column("rejected_records", sa.Integer(), server_default="0", nullable=False),
        sa.Column("duplicate_source_records", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("mapping_version", sa.String(length=80), nullable=False),
        sa.Column("configuration_version", sa.String(length=80), server_default="day4.v1", nullable=False),
        sa.Column("initiated_by", sa.String(length=120), server_default="day4-cli", nullable=False),
        sa.Column("provenance", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.CheckConstraint("status in ('PENDING','RUNNING','COMPLETED','COMPLETED_WITH_WARNINGS','FAILED','ALREADY_INGESTED')", name="ingestion_run_status_allowed"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name=op.f("fk_ingestion_runs_tenant_id_tenants")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ingestion_runs")),
    )
    op.create_table(
        "source_mappings",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("source_system", sa.String(length=80), nullable=False),
        sa.Column("record_type", sa.String(length=80), nullable=False),
        sa.Column("mapping_version", sa.String(length=80), nullable=False),
        sa.Column("schema_version", sa.String(length=80), nullable=False),
        sa.Column("field_mappings", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("required_source_fields", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("timestamp_semantics", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_source_mappings")),
        sa.UniqueConstraint("source_system", "record_type", "mapping_version", name="uq_source_mappings_identity"),
    )
    op.create_table(
        "staged_source_records",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("ingestion_run_id", sa.UUID(), nullable=False),
        sa.Column("source_system", sa.String(length=80), nullable=False),
        sa.Column("source_type", sa.String(length=80), nullable=False),
        sa.Column("record_type", sa.String(length=80), nullable=False),
        sa.Column("source_file", sa.Text(), nullable=False),
        sa.Column("source_row_index", sa.Integer(), nullable=True),
        sa.Column("source_record_id", sa.String(length=255), nullable=False),
        sa.Column("source_record_version", sa.String(length=120), nullable=True),
        sa.Column("source_checksum", sa.String(length=64), nullable=False),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("parsed_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("candidate_canonical_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("source_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("effective_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("recorded_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ingestion_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("data_quality_status", sa.String(length=40), nullable=False),
        sa.Column("mapping_version", sa.String(length=80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("data_quality_status in ('ACCEPTED','ACCEPTED_WITH_WARNINGS','REJECTED','SKIPPED_DUPLICATE_SOURCE')", name="staged_record_quality_status_allowed"),
        sa.ForeignKeyConstraint(["ingestion_run_id"], ["ingestion_runs.id"], name=op.f("fk_staged_source_records_ingestion_run_id_ingestion_runs")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name=op.f("fk_staged_source_records_tenant_id_tenants")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_staged_source_records")),
        sa.UniqueConstraint("tenant_id", "source_system", "source_file", "source_record_id", "source_checksum", name="uq_staged_source_record_identity"),
    )
    op.create_table(
        "data_quality_issues",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("ingestion_run_id", sa.UUID(), nullable=False),
        sa.Column("staged_source_record_id", sa.UUID(), nullable=True),
        sa.Column("issue_code", sa.String(length=80), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("field", sa.String(length=120), nullable=True),
        sa.Column("observed_value", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=40), server_default="open", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("severity in ('INFO','WARNING','ERROR')", name="data_quality_issue_severity_allowed"),
        sa.ForeignKeyConstraint(["ingestion_run_id"], ["ingestion_runs.id"], name=op.f("fk_data_quality_issues_ingestion_run_id_ingestion_runs")),
        sa.ForeignKeyConstraint(["staged_source_record_id"], ["staged_source_records.id"], name=op.f("fk_data_quality_issues_staged_source_record_id_staged_source_records")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], name=op.f("fk_data_quality_issues_tenant_id_tenants")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_data_quality_issues")),
    )
    op.create_index("ix_ingestion_runs_source_file_checksum", "ingestion_runs", ["source_system", "source_file", "source_checksum"])
    op.create_index("ix_staged_source_records_run", "staged_source_records", ["ingestion_run_id"])
    op.create_index("ix_staged_source_records_source", "staged_source_records", ["source_system", "record_type", "source_record_id"])


def downgrade() -> None:
    op.drop_index("ix_staged_source_records_source", table_name="staged_source_records")
    op.drop_index("ix_staged_source_records_run", table_name="staged_source_records")
    op.drop_index("ix_ingestion_runs_source_file_checksum", table_name="ingestion_runs")
    op.drop_table("data_quality_issues")
    op.drop_table("staged_source_records")
    op.drop_table("source_mappings")
    op.drop_table("ingestion_runs")
