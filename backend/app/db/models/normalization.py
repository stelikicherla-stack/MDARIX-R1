import uuid

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


def uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))


def tz(nullable: bool = True) -> Mapped[object]:
    return mapped_column(DateTime(timezone=True), nullable=nullable)


class NormalizationRun(Base):
    __tablename__ = "normalization_runs"

    id = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    normalization_version: Mapped[str] = mapped_column(String(80), nullable=False)
    rule_set_version: Mapped[str] = mapped_column(String(80), nullable=False)
    started_at = tz(False)
    completed_at = tz()
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    records_processed: Mapped[int] = mapped_column(nullable=False, server_default="0")
    canonical_objects_created: Mapped[int] = mapped_column(nullable=False, server_default="0")
    records_matched: Mapped[int] = mapped_column(nullable=False, server_default="0")
    links_created: Mapped[int] = mapped_column(nullable=False, server_default="0")
    relationships_resolved: Mapped[int] = mapped_column(nullable=False, server_default="0")
    ambiguous_records: Mapped[int] = mapped_column(nullable=False, server_default="0")
    unresolved_records: Mapped[int] = mapped_column(nullable=False, server_default="0")
    conflicts: Mapped[int] = mapped_column(nullable=False, server_default="0")
    warnings: Mapped[int] = mapped_column(nullable=False, server_default="0")
    errors: Mapped[int] = mapped_column(nullable=False, server_default="0")
    provenance: Mapped[dict | None] = mapped_column(JSONB)

    __table_args__ = (
        CheckConstraint("status in ('RUNNING','COMPLETED','COMPLETED_WITH_WARNINGS','FAILED')", name="normalization_run_status_allowed"),
        Index("ix_normalization_runs_tenant_started", "tenant_id", "started_at"),
    )


class IdentityRule(Base):
    __tablename__ = "identity_rules"

    id = uuid_pk()
    rule_id: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    version: Mapped[str] = mapped_column(String(40), nullable=False)
    precedence: Mapped[int] = mapped_column(nullable=False)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    match_conditions: Mapped[dict] = mapped_column(JSONB, nullable=False)
    ambiguity_behavior: Mapped[str] = mapped_column(Text, nullable=False)
    active: Mapped[bool] = mapped_column(nullable=False, server_default="true")
    created_at = tz(False)

    __table_args__ = (
        UniqueConstraint("rule_id", "version", name="uq_identity_rules_rule_version"),
        Index("ix_identity_rules_entity_precedence", "entity_type", "precedence"),
    )


class SourceCanonicalLink(Base):
    __tablename__ = "source_canonical_links"

    id = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    normalization_run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("normalization_runs.id"), nullable=False)
    staged_source_record_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("staged_source_records.id"), nullable=False)
    canonical_entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    canonical_entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    canonical_business_identifier: Mapped[str | None] = mapped_column(String(255))
    source_value: Mapped[str | None] = mapped_column(Text)
    normalized_value: Mapped[str | None] = mapped_column(Text)
    resolution_method: Mapped[str] = mapped_column(String(80), nullable=False)
    resolution_rule: Mapped[str] = mapped_column(String(120), nullable=False)
    resolution_status: Mapped[str] = mapped_column(String(40), nullable=False)
    confidence_category: Mapped[str] = mapped_column(String(40), nullable=False)
    human_review_status: Mapped[str] = mapped_column(String(40), nullable=False, server_default="not_required")
    evidence_context: Mapped[dict | None] = mapped_column(JSONB)
    provenance: Mapped[dict | None] = mapped_column(JSONB)
    resolved_at = tz(False)
    updated_at = tz(False)

    __table_args__ = (
        CheckConstraint("resolution_status in ('MATCHED','NEW_CANONICAL_OBJECT','AMBIGUOUS','UNRESOLVED','CONFLICT','REQUIRES_HUMAN_REVIEW')", name="source_canonical_link_status_allowed"),
        CheckConstraint("confidence_category in ('DETERMINISTIC','AMBIGUOUS','UNRESOLVED','CONFLICT')", name="source_canonical_link_confidence_allowed"),
        UniqueConstraint("tenant_id", "staged_source_record_id", "canonical_entity_type", "resolution_rule", name="uq_source_canonical_link_identity"),
        Index("ix_source_canonical_links_entity", "tenant_id", "canonical_entity_type", "canonical_entity_id"),
        Index("ix_source_canonical_links_status", "tenant_id", "resolution_status"),
    )


class CanonicalRelationship(Base):
    __tablename__ = "canonical_relationships"

    id = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    normalization_run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("normalization_runs.id"), nullable=False)
    source_link_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("source_canonical_links.id"))
    source_entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    source_entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    target_entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    target_entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(120), nullable=False)
    resolution_rule: Mapped[str] = mapped_column(String(120), nullable=False)
    assertion_status: Mapped[str] = mapped_column(String(40), nullable=False)
    effective_timestamp = tz()
    recorded_timestamp = tz()
    provenance: Mapped[dict | None] = mapped_column(JSONB)
    created_at = tz(False)

    __table_args__ = (
        CheckConstraint("assertion_status in ('supported','contradicted','hypothesized','unknown')", name="canonical_relationship_assertion_allowed"),
        UniqueConstraint("tenant_id", "source_entity_type", "source_entity_id", "target_entity_type", "target_entity_id", "relationship_type", name="uq_canonical_relationship_identity"),
        Index("ix_canonical_relationships_lookup", "tenant_id", "source_entity_type", "source_entity_id"),
    )


class NormalizationIssue(Base):
    __tablename__ = "normalization_issues"

    id = uuid_pk()
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    normalization_run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("normalization_runs.id"), nullable=False)
    staged_source_record_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("staged_source_records.id"))
    issue_code: Mapped[str] = mapped_column(String(80), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(Text, nullable=False)
    provenance: Mapped[dict | None] = mapped_column(JSONB)
    created_at = tz(False)

    __table_args__ = (
        CheckConstraint("severity in ('INFO','WARNING','ERROR')", name="normalization_issue_severity_allowed"),
        Index("ix_normalization_issues_run", "normalization_run_id"),
    )
