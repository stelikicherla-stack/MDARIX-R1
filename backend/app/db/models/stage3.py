import uuid
from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.base import Base
from backend.app.db.models.foundation import tz, tenant_fk, uuid_pk


class AIInteractionSession(Base):
    __tablename__ = "ai_interaction_sessions"
    id = uuid_pk(); tenant_id = tenant_fk(); user_id: Mapped[str] = mapped_column(String(255), nullable=False)
    membership_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True)); role_id: Mapped[str | None] = mapped_column(String(120))
    page_context: Mapped[str | None] = mapped_column(String(120)); correlation_id: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="ACTIVE"); created_at = tz(False); updated_at = tz(False)


class AIInteraction(Base):
    __tablename__ = "ai_interactions"
    id = uuid_pk(); tenant_id = tenant_fk(); session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False); product_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True)); product_version_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True)); investigation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    user_prompt: Mapped[str] = mapped_column(Text, nullable=False); normalized_intent: Mapped[str | None] = mapped_column(String(120)); temporal_mode: Mapped[str | None] = mapped_column(String(30)); temporal_cutoff = tz(True)
    response: Mapped[dict] = mapped_column(JSONB, nullable=False); provenance: Mapped[dict | None] = mapped_column(JSONB); correlation_id: Mapped[str] = mapped_column(String(120), nullable=False); created_at = tz(False)


class AIInteractionFeedback(Base):
    __tablename__ = "ai_interaction_feedback"
    id = uuid_pk(); tenant_id = tenant_fk(); interaction_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False); user_id: Mapped[str] = mapped_column(String(255), nullable=False); feedback: Mapped[dict] = mapped_column(JSONB, nullable=False); created_at = tz(False)


class ContextSnapshot(Base):
    __tablename__ = "context_snapshots"
    id = uuid_pk(); tenant_id = tenant_fk(); decision_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False); decision_version: Mapped[str] = mapped_column(String(80), nullable=False); snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False); created_by: Mapped[str] = mapped_column(String(255), nullable=False); created_at = tz(False)
    __table_args__ = (UniqueConstraint("tenant_id", "decision_id", "decision_version", name="uq_context_snapshot_version"),)


class InboundEmailEvent(Base):
    __tablename__ = "inbound_email_events"
    id = uuid_pk(); tenant_id = tenant_fk(nullable=True); provider_event_id: Mapped[str] = mapped_column(String(255), nullable=False); event_type: Mapped[str] = mapped_column(String(100), nullable=False); status: Mapped[str] = mapped_column(String(50), nullable=False); event_metadata: Mapped[dict | None] = mapped_column("metadata", JSONB); created_at = tz(False)
    __table_args__ = (UniqueConstraint("provider_event_id", name="uq_inbound_email_provider_event"),)

class SupplierEvidenceRequest(Base):
    __tablename__ = "supplier_evidence_requests"
    id = uuid_pk(); tenant_id = tenant_fk(); investigation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True)); supplier_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True)); requested_by: Mapped[str] = mapped_column(String(255), nullable=False); recipient: Mapped[str] = mapped_column(String(254), nullable=False); title: Mapped[str] = mapped_column(String(240), nullable=False); requested_items: Mapped[dict] = mapped_column(JSONB, nullable=False); status: Mapped[str] = mapped_column(String(40), nullable=False, server_default="PENDING_DELIVERY"); provider_message_id: Mapped[str | None] = mapped_column(String(255)); created_at = tz(False); updated_at = tz(False)

class EvidenceAttachment(Base):
    __tablename__ = "evidence_attachments"
    id = uuid_pk(); tenant_id = tenant_fk(); request_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True)); uploaded_by: Mapped[str] = mapped_column(String(255), nullable=False); filename: Mapped[str] = mapped_column(String(255), nullable=False); content_type: Mapped[str] = mapped_column(String(120), nullable=False); object_key: Mapped[str] = mapped_column(String(500), nullable=False); size: Mapped[int] = mapped_column(nullable=False); checksum: Mapped[str] = mapped_column(String(64), nullable=False); created_at = tz(False)
