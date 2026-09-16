import uuid

from sqlalchemy import CheckConstraint, DateTime, ForeignKeyConstraint, Index, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base
from backend.app.db.models.foundation import Vector, tenant_fk, uuid_pk


EMBEDDING_DIMENSION = 32
EMBEDDING_PROVIDER = "mdarix-deterministic"
EMBEDDING_MODEL = "mdarix-hash-bow-32"
EMBEDDING_MODEL_VERSION = "1.0"
EMBEDDING_PIPELINE_VERSION = "R1-Day9"
RETRIEVAL_CONFIG_VERSION = "R1-Day9"


def now_tz():
    return mapped_column(DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))


class EvidenceChunkEmbedding(Base):
    __tablename__ = "evidence_chunk_embeddings"

    id = uuid_pk()
    tenant_id = tenant_fk()
    evidence_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    chunk_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    chunk_checksum: Mapped[str] = mapped_column(String(128), nullable=False)
    provider: Mapped[str] = mapped_column(String(120), nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(120), nullable=False)
    model_version: Mapped[str] = mapped_column(String(120), nullable=False)
    embedding_dimension: Mapped[int] = mapped_column(nullable=False)
    pipeline_version: Mapped[str] = mapped_column(String(120), nullable=False)
    distance_metric: Mapped[str] = mapped_column(String(40), nullable=False, server_default="cosine")
    embedding: Mapped[object | None] = mapped_column(Vector(EMBEDDING_DIMENSION))
    indexing_status: Mapped[str] = mapped_column(String(40), nullable=False, server_default="INDEXED")
    failure_reason: Mapped[str | None] = mapped_column(Text)
    created_at = now_tz()

    __table_args__ = (
        ForeignKeyConstraint(["tenant_id", "evidence_id"], ["evidence.tenant_id", "evidence.id"]),
        ForeignKeyConstraint(["tenant_id", "chunk_id"], ["evidence_chunks.tenant_id", "evidence_chunks.id"]),
        CheckConstraint("indexing_status in ('INDEXED','FAILED')", name="chunk_embedding_status_allowed"),
        UniqueConstraint(
            "tenant_id",
            "chunk_id",
            "chunk_checksum",
            "embedding_model",
            "model_version",
            "pipeline_version",
            name="uq_evidence_chunk_embedding_version",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_evidence_chunk_embeddings_tenant_id_id"),
    )


class RetrievalQuery(Base):
    __tablename__ = "retrieval_queries"

    id = uuid_pk()
    tenant_id = tenant_fk()
    investigation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    retrieval_mode: Mapped[str] = mapped_column(String(40), nullable=False)
    temporal_mode: Mapped[str] = mapped_column(String(40), nullable=False, server_default="current")
    filters: Mapped[dict | None] = mapped_column(JSONB)
    embedding_model: Mapped[str | None] = mapped_column(String(120))
    embedding_model_version: Mapped[str | None] = mapped_column(String(120))
    retrieval_config_version: Mapped[str] = mapped_column(String(120), nullable=False)
    top_k: Mapped[int] = mapped_column(nullable=False)
    returned_refs: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    created_at = now_tz()

    __table_args__ = (
        ForeignKeyConstraint(["tenant_id", "investigation_id"], ["investigations.tenant_id", "investigations.id"]),
        CheckConstraint("retrieval_mode in ('structured','semantic','hybrid')", name="retrieval_mode_allowed"),
        CheckConstraint("temporal_mode in ('current','event','known')", name="retrieval_temporal_mode_allowed"),
        CheckConstraint("status in ('COMPLETED','NO_RELEVANT_EVIDENCE','INSUFFICIENT_RELEVANT_EVIDENCE','FAILED')", name="retrieval_status_allowed"),
        UniqueConstraint("tenant_id", "id", name="uq_retrieval_queries_tenant_id_id"),
    )


Index("ix_chunk_embeddings_tenant_chunk", EvidenceChunkEmbedding.tenant_id, EvidenceChunkEmbedding.chunk_id)
Index("ix_chunk_embeddings_tenant_status", EvidenceChunkEmbedding.tenant_id, EvidenceChunkEmbedding.indexing_status)
Index("ix_retrieval_queries_tenant_created", RetrievalQuery.tenant_id, RetrievalQuery.created_at)
