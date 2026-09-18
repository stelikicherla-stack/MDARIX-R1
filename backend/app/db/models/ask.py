import uuid
from sqlalchemy import DateTime, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.db.base import Base


class InvestigationSessionRecord(Base):
    __tablename__ = "investigation_sessions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    owner_user_id: Mapped[str] = mapped_column(String(254), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="ACTIVE")
    active_product_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    active_product_version_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    temporal_context: Mapped[dict | None] = mapped_column(JSONB)
    previous_query_id: Mapped[str | None] = mapped_column(String(120))
    policy_provenance: Mapped[dict | None] = mapped_column(JSONB)
    correlation_id: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at = mapped_column(DateTime(timezone=True), nullable=False)
