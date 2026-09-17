import uuid
from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.base import Base
from .foundation import tenant_fk, uuid_pk, tz

class ConnectorRun(Base):
    __tablename__ = "connector_runs"
    id = uuid_pk(); tenant_id = tenant_fk(); connection_id: Mapped[str] = mapped_column(String(160), nullable=False); source_system: Mapped[str] = mapped_column(String(120), nullable=False); run_type: Mapped[str] = mapped_column(String(40), nullable=False, server_default="INCREMENTAL"); status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="PENDING")
    records_received: Mapped[int] = mapped_column(nullable=False, server_default="0"); records_accepted: Mapped[int] = mapped_column(nullable=False, server_default="0"); records_rejected: Mapped[int] = mapped_column(nullable=False, server_default="0"); records_quarantined: Mapped[int] = mapped_column(nullable=False, server_default="0"); records_duplicate: Mapped[int] = mapped_column(nullable=False, server_default="0"); retry_attempt: Mapped[int] = mapped_column(nullable=False, server_default="0")
    reconciliation_status: Mapped[str | None] = mapped_column(String(40)); schema_drift_status: Mapped[str | None] = mapped_column(String(40)); failure_category: Mapped[str | None] = mapped_column(String(60)); correlation_id: Mapped[str | None] = mapped_column(String(120)); started_at = tz(False); completed_at = tz(); created_at = tz(False)

class ConnectorSourceRecord(Base):
    __tablename__ = "connector_source_records"
    id = uuid_pk(); tenant_id = tenant_fk(); connector_run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("connector_runs.id"), nullable=False); source_system: Mapped[str] = mapped_column(String(120), nullable=False); source_record_id: Mapped[str] = mapped_column(String(255), nullable=False); source_record_version: Mapped[str | None] = mapped_column(String(120)); fingerprint: Mapped[str] = mapped_column(String(64), nullable=False); processing_status: Mapped[str] = mapped_column(String(40), nullable=False); quarantine_reason: Mapped[str | None] = mapped_column(Text); effective_at = tz(); ingested_at = tz(False); created_at = tz(False)
    __table_args__ = (UniqueConstraint("tenant_id", "source_system", "source_record_id", "source_record_version", name="uq_connector_source_record_identity"),)

class ReconciliationRecord(Base):
    __tablename__ = "connector_reconciliations"
    id = uuid_pk(); tenant_id = tenant_fk(); connector_run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("connector_runs.id"), nullable=False); expected_count: Mapped[int] = mapped_column(nullable=False); received_count: Mapped[int] = mapped_column(nullable=False); accepted_count: Mapped[int] = mapped_column(nullable=False); rejected_count: Mapped[int] = mapped_column(nullable=False); quarantined_count: Mapped[int] = mapped_column(nullable=False); duplicate_count: Mapped[int] = mapped_column(nullable=False); unresolved_count: Mapped[int] = mapped_column(nullable=False, server_default="0"); status: Mapped[str] = mapped_column(String(40), nullable=False); details: Mapped[dict | None] = mapped_column(JSONB); reconciled_at = tz(False)
