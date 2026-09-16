import uuid

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


def uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))


def tz(nullable: bool = True) -> Mapped[object]:
    return mapped_column(DateTime(timezone=True), nullable=nullable)


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    source_system: Mapped[str] = mapped_column(String(80), nullable=False)
    source_type: Mapped[str] = mapped_column(String(80), nullable=False)
    source_file: Mapped[str] = mapped_column(Text, nullable=False)
    source_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    ingestion_started_at = tz(False)
    ingestion_completed_at = tz()
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    total_records: Mapped[int] = mapped_column(nullable=False, server_default="0")
    accepted_records: Mapped[int] = mapped_column(nullable=False, server_default="0")
    warning_records: Mapped[int] = mapped_column(nullable=False, server_default="0")
    rejected_records: Mapped[int] = mapped_column(nullable=False, server_default="0")
    duplicate_source_records: Mapped[int] = mapped_column(nullable=False, server_default="0")
    error_summary: Mapped[str | None] = mapped_column(Text)
    mapping_version: Mapped[str] = mapped_column(String(80), nullable=False)
    configuration_version: Mapped[str] = mapped_column(String(80), nullable=False, server_default="day4.v1")
    initiated_by: Mapped[str] = mapped_column(String(120), nullable=False, server_default="day4-cli")
    provenance: Mapped[dict | None] = mapped_column(JSONB)

    __table_args__ = (
        CheckConstraint("status in ('PENDING','RUNNING','COMPLETED','COMPLETED_WITH_WARNINGS','FAILED','ALREADY_INGESTED')", name="ingestion_run_status_allowed"),
        Index("ix_ingestion_runs_source_file_checksum", "source_system", "source_file", "source_checksum"),
    )


class SourceMapping(Base):
    __tablename__ = "source_mappings"

    id = uuid_pk()
    source_system: Mapped[str] = mapped_column(String(80), nullable=False)
    record_type: Mapped[str] = mapped_column(String(80), nullable=False)
    mapping_version: Mapped[str] = mapped_column(String(80), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(80), nullable=False)
    field_mappings: Mapped[dict] = mapped_column(JSONB, nullable=False)
    required_source_fields: Mapped[dict] = mapped_column(JSONB, nullable=False)
    timestamp_semantics: Mapped[dict | None] = mapped_column(JSONB)
    created_at = tz(False)

    __table_args__ = (
        UniqueConstraint("source_system", "record_type", "mapping_version", name="uq_source_mappings_identity"),
    )


class StagedSourceRecord(Base):
    __tablename__ = "staged_source_records"

    id = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    ingestion_run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ingestion_runs.id"), nullable=False)
    source_system: Mapped[str] = mapped_column(String(80), nullable=False)
    source_type: Mapped[str] = mapped_column(String(80), nullable=False)
    record_type: Mapped[str] = mapped_column(String(80), nullable=False)
    source_file: Mapped[str] = mapped_column(Text, nullable=False)
    source_row_index: Mapped[int | None] = mapped_column()
    source_record_id: Mapped[str] = mapped_column(String(255), nullable=False)
    source_record_version: Mapped[str | None] = mapped_column(String(120))
    source_checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    raw_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    parsed_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    candidate_canonical_payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    source_timestamp = tz()
    effective_timestamp = tz()
    recorded_timestamp = tz()
    ingestion_timestamp = tz(False)
    data_quality_status: Mapped[str] = mapped_column(String(40), nullable=False)
    mapping_version: Mapped[str] = mapped_column(String(80), nullable=False)
    created_at = tz(False)

    __table_args__ = (
        CheckConstraint("data_quality_status in ('ACCEPTED','ACCEPTED_WITH_WARNINGS','REJECTED','SKIPPED_DUPLICATE_SOURCE')", name="staged_record_quality_status_allowed"),
        UniqueConstraint("tenant_id", "source_system", "source_file", "source_record_id", "source_checksum", name="uq_staged_source_record_identity"),
        Index("ix_staged_source_records_run", "ingestion_run_id"),
        Index("ix_staged_source_records_source", "source_system", "record_type", "source_record_id"),
    )


class DataQualityIssue(Base):
    __tablename__ = "data_quality_issues"

    id = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    ingestion_run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ingestion_runs.id"), nullable=False)
    staged_source_record_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("staged_source_records.id"))
    issue_code: Mapped[str] = mapped_column(String(80), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    field: Mapped[str | None] = mapped_column(String(120))
    observed_value: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, server_default="open")
    created_at = tz(False)

    __table_args__ = (
        CheckConstraint("severity in ('INFO','WARNING','ERROR')", name="data_quality_issue_severity_allowed"),
    )
