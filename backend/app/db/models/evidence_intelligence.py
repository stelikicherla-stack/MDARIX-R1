import uuid

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base
from backend.app.db.models.foundation import tenant_fk, tz, uuid_pk


def now_tz():
    return mapped_column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))


class EvidenceChunk(Base):
    __tablename__ = "evidence_chunks"

    id = uuid_pk()
    tenant_id = tenant_fk()
    evidence_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    sequence_number: Mapped[int] = mapped_column(nullable=False)
    text_content: Mapped[str] = mapped_column(Text, nullable=False)
    source_anchor: Mapped[dict | None] = mapped_column(JSONB)
    token_count: Mapped[int | None] = mapped_column()
    checksum: Mapped[str | None] = mapped_column(String(128))
    created_at = now_tz()

    __table_args__ = (
        ForeignKeyConstraint(["tenant_id", "evidence_id"], ["evidence.tenant_id", "evidence.id"]),
        UniqueConstraint("tenant_id", "evidence_id", "sequence_number", name="uq_evidence_chunks_sequence"),
        UniqueConstraint("tenant_id", "id", name="uq_evidence_chunks_tenant_id_id"),
    )


class EvidenceObservation(Base):
    __tablename__ = "evidence_observations"

    id = uuid_pk()
    tenant_id = tenant_fk()
    evidence_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    chunk_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    observation_type: Mapped[str] = mapped_column(String(80), nullable=False, server_default="AI_EXTRACTED_OBSERVATION")
    extraction_method: Mapped[str] = mapped_column(String(40), nullable=False, server_default="DETERMINISTIC")
    source_anchor: Mapped[dict | None] = mapped_column(JSONB)
    effective_context: Mapped[dict | None] = mapped_column(JSONB)
    quality_status: Mapped[str] = mapped_column(String(40), nullable=False, server_default="VALIDATED")
    limitations: Mapped[dict | None] = mapped_column(JSONB)
    ai_execution_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at = now_tz()

    __table_args__ = (
        ForeignKeyConstraint(["tenant_id", "evidence_id"], ["evidence.tenant_id", "evidence.id"]),
        ForeignKeyConstraint(["tenant_id", "chunk_id"], ["evidence_chunks.tenant_id", "evidence_chunks.id"]),
        ForeignKeyConstraint(["tenant_id", "ai_execution_id"], ["ai_executions.tenant_id", "ai_executions.id"]),
        CheckConstraint(
            "observation_type in ('EXPLICIT_SOURCE_STATEMENT','STRUCTURED_EXTRACTION','DETERMINISTIC_DERIVATION','AI_EXTRACTED_OBSERVATION')",
            name="evidence_obs_type_allowed",
        ),
        CheckConstraint(
            "extraction_method in ('DETERMINISTIC','GENAI')",
            name="evidence_obs_method_allowed",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_evidence_observations_tenant_id_id"),
    )


class EvidenceEntityLink(Base):
    __tablename__ = "evidence_entity_links"

    id = uuid_pk()
    tenant_id = tenant_fk()
    evidence_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    observation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    raw_reference: Mapped[str | None] = mapped_column(Text)
    resolution_status: Mapped[str] = mapped_column(String(40), nullable=False, server_default="RESOLVED")
    confidence_score: Mapped[str | None] = mapped_column(String(40))
    created_at = now_tz()

    __table_args__ = (
        ForeignKeyConstraint(["tenant_id", "evidence_id"], ["evidence.tenant_id", "evidence.id"]),
        ForeignKeyConstraint(["tenant_id", "observation_id"], ["evidence_observations.tenant_id", "evidence_observations.id"]),
        CheckConstraint("resolution_status in ('RESOLVED','UNRESOLVED')", name="evidence_entity_link_status_allowed"),
        UniqueConstraint("tenant_id", "id", name="uq_evidence_entity_links_tenant_id_id"),
    )


class EvidencePropositionRelation(Base):
    __tablename__ = "evidence_proposition_relations"

    id = uuid_pk()
    tenant_id = tenant_fk()
    observation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    proposition_text: Mapped[str] = mapped_column(Text, nullable=False)
    relation_type: Mapped[str] = mapped_column(String(40), nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text)
    created_at = now_tz()


    __table_args__ = (
        ForeignKeyConstraint(["tenant_id", "observation_id"], ["evidence_observations.tenant_id", "evidence_observations.id"]),
        CheckConstraint("relation_type in ('SUPPORT','CONTRADICT','NEUTRAL_CONTEXTUAL')", name="evidence_prop_relation_type_allowed"),
        UniqueConstraint("tenant_id", "id", name="uq_evidence_proposition_relations_tenant_id_id"),
    )


Index("ix_evidence_chunks_tenant_evidence", EvidenceChunk.tenant_id, EvidenceChunk.evidence_id)
Index("ix_evidence_observations_tenant_evidence", EvidenceObservation.tenant_id, EvidenceObservation.evidence_id)
Index("ix_evidence_entity_links_tenant_evidence", EvidenceEntityLink.tenant_id, EvidenceEntityLink.evidence_id)
