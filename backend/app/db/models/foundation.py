import uuid

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import UserDefinedType

from backend.app.db.base import Base


class Vector(UserDefinedType):
    cache_ok = True

    def __init__(self, dimensions: int):
        self.dimensions = dimensions

    def get_col_spec(self, **kw: object) -> str:
        return f"vector({self.dimensions})"


def uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))


def tenant_fk(nullable: bool = False) -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=nullable)


def tz(nullable: bool = True) -> Mapped[object]:
    return mapped_column(DateTime(timezone=True), nullable=nullable)


class Tenant(Base):
    __tablename__ = "tenants"
    id = uuid_pk()
    tenant_key: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, server_default="active")
    created_at = tz(False)
    updated_at = tz(False)


class SourceRecord(Base):
    __tablename__ = "source_records"
    id = uuid_pk()
    tenant_id = tenant_fk()
    source_system: Mapped[str] = mapped_column(String(120), nullable=False)
    source_record_id: Mapped[str] = mapped_column(String(255), nullable=False)
    source_record_version: Mapped[str | None] = mapped_column(String(120))
    raw_payload_ref: Mapped[str | None] = mapped_column(Text)
    source_timestamp = tz()
    effective_timestamp = tz()
    ingestion_timestamp = tz(False)
    checksum: Mapped[str | None] = mapped_column(String(128))
    data_quality_status: Mapped[str] = mapped_column(String(40), nullable=False, server_default="unreviewed")
    created_at = tz(False)
    __table_args__ = (
        UniqueConstraint("tenant_id", "source_system", "source_record_id", "source_record_version", name="uq_source_record_identity"),
        UniqueConstraint("tenant_id", "id", name="uq_source_records_tenant_id_id"),
    )


class TenantOwned:
    id = uuid_pk()
    tenant_id = tenant_fk()
    source_record_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("source_records.id"))
    source_system: Mapped[str | None] = mapped_column(String(120))
    source_identifier: Mapped[str | None] = mapped_column(String(255))
    source_timestamp = tz()
    effective_timestamp = tz()
    recorded_timestamp = tz()
    ingestion_timestamp = tz()
    created_at = tz(False)
    updated_at = tz(False)


class Product(TenantOwned, Base):
    __tablename__ = "products"
    product_identifier: Mapped[str] = mapped_column(String(120), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    lifecycle_status: Mapped[str] = mapped_column(String(40), nullable=False, server_default="active")
    product_family: Mapped[str | None] = mapped_column(String(120))
    manufacturer_context: Mapped[str | None] = mapped_column(String(255))
    __table_args__ = (
        UniqueConstraint("tenant_id", "product_identifier", name="uq_products_tenant_product_identifier"),
        UniqueConstraint("tenant_id", "id", name="uq_products_tenant_id_id"),
    )


class ProductVersion(TenantOwned, Base):
    __tablename__ = "product_versions"
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    version_identifier: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    lifecycle_status: Mapped[str] = mapped_column(String(40), nullable=False, server_default="active")
    release_timestamp = tz()
    __table_args__ = (
        ForeignKeyConstraint(["tenant_id", "product_id"], ["products.tenant_id", "products.id"]),
        UniqueConstraint("tenant_id", "product_id", "version_identifier", name="uq_product_versions_tenant_product_version"),
        UniqueConstraint("tenant_id", "id", name="uq_product_versions_tenant_id_id"),
    )


class Component(TenantOwned, Base):
    __tablename__ = "components"
    component_identifier: Mapped[str] = mapped_column(String(120), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    revision: Mapped[str | None] = mapped_column(String(80))
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), nullable=False, server_default="active")
    __table_args__ = (
        UniqueConstraint("tenant_id", "component_identifier", "revision", name="uq_components_tenant_identifier_revision"),
        UniqueConstraint("tenant_id", "id", name="uq_components_tenant_id_id"),
    )


class Supplier(TenantOwned, Base):
    __tablename__ = "suppliers"
    supplier_identifier: Mapped[str] = mapped_column(String(120), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, server_default="active")
    __table_args__ = (
        UniqueConstraint("tenant_id", "supplier_identifier", name="uq_suppliers_tenant_supplier_identifier"),
        UniqueConstraint("tenant_id", "id", name="uq_suppliers_tenant_id_id"),
    )


class ManufacturingSite(TenantOwned, Base):
    __tablename__ = "manufacturing_sites"
    site_identifier: Mapped[str] = mapped_column(String(120), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(40), nullable=False, server_default="active")
    __table_args__ = (
        UniqueConstraint("tenant_id", "site_identifier", name="uq_sites_tenant_site_identifier"),
        UniqueConstraint("tenant_id", "id", name="uq_manufacturing_sites_tenant_id_id"),
    )


class LotBatch(TenantOwned, Base):
    __tablename__ = "lot_batches"
    lot_identifier: Mapped[str] = mapped_column(String(120), nullable=False)
    product_version_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    manufacturing_site_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    status: Mapped[str] = mapped_column(String(40), nullable=False, server_default="active")
    __table_args__ = (
        ForeignKeyConstraint(["tenant_id", "product_version_id"], ["product_versions.tenant_id", "product_versions.id"]),
        ForeignKeyConstraint(["tenant_id", "manufacturing_site_id"], ["manufacturing_sites.tenant_id", "manufacturing_sites.id"]),
        UniqueConstraint("tenant_id", "lot_identifier", name="uq_lots_tenant_lot_identifier"),
        UniqueConstraint("tenant_id", "id", name="uq_lot_batches_tenant_id_id"),
    )


class Requirement(TenantOwned, Base):
    __tablename__ = "requirements"
    product_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    product_version_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    requirement_identifier: Mapped[str] = mapped_column(String(120), nullable=False)
    requirement_type: Mapped[str | None] = mapped_column(String(80))
    text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, server_default="active")
    __table_args__ = (
        ForeignKeyConstraint(["tenant_id", "product_id"], ["products.tenant_id", "products.id"]),
        ForeignKeyConstraint(["tenant_id", "product_version_id"], ["product_versions.tenant_id", "product_versions.id"]),
        UniqueConstraint("tenant_id", "requirement_identifier", name="uq_requirements_tenant_identifier"),
        UniqueConstraint("tenant_id", "id", name="uq_requirements_tenant_id_id"),
    )


class Change(TenantOwned, Base):
    __tablename__ = "changes"
    change_identifier: Mapped[str] = mapped_column(String(120), nullable=False)
    change_type: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    event_timestamp = tz()
    __table_args__ = (
        UniqueConstraint("tenant_id", "change_identifier", name="uq_changes_tenant_identifier"),
        UniqueConstraint("tenant_id", "id", name="uq_changes_tenant_id_id"),
    )


class Complaint(TenantOwned, Base):
    __tablename__ = "complaints"
    complaint_identifier: Mapped[str] = mapped_column(String(120), nullable=False)
    product_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    product_version_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    lot_batch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    event_timestamp = tz()
    complaint_timestamp = tz()
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, server_default="open")
    __table_args__ = (
        ForeignKeyConstraint(["tenant_id", "product_id"], ["products.tenant_id", "products.id"]),
        ForeignKeyConstraint(["tenant_id", "product_version_id"], ["product_versions.tenant_id", "product_versions.id"]),
        ForeignKeyConstraint(["tenant_id", "lot_batch_id"], ["lot_batches.tenant_id", "lot_batches.id"]),
        UniqueConstraint("tenant_id", "complaint_identifier", name="uq_complaints_tenant_identifier"),
        UniqueConstraint("tenant_id", "id", name="uq_complaints_tenant_id_id"),
    )


class Investigation(TenantOwned, Base):
    __tablename__ = "investigations"
    investigation_identifier: Mapped[str] = mapped_column(String(120), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    investigation_question: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, server_default="open")
    opened_at = tz()
    closed_at = tz()
    owner_ref: Mapped[str | None] = mapped_column(String(255))
    __table_args__ = (
        ForeignKeyConstraint(["tenant_id", "product_id"], ["products.tenant_id", "products.id"]),
        UniqueConstraint("tenant_id", "investigation_identifier", name="uq_investigations_tenant_identifier"),
        UniqueConstraint("tenant_id", "id", name="uq_investigations_tenant_id_id"),
    )


class Risk(TenantOwned, Base):
    __tablename__ = "risks"
    risk_identifier: Mapped[str] = mapped_column(String(120), nullable=False)
    product_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    product_version_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, server_default="active")
    __table_args__ = (
        ForeignKeyConstraint(["tenant_id", "product_id"], ["products.tenant_id", "products.id"]),
        ForeignKeyConstraint(["tenant_id", "product_version_id"], ["product_versions.tenant_id", "product_versions.id"]),
        UniqueConstraint("tenant_id", "risk_identifier", name="uq_risks_tenant_identifier"),
        UniqueConstraint("tenant_id", "id", name="uq_risks_tenant_id_id"),
    )


class FailureMode(TenantOwned, Base):
    __tablename__ = "failure_modes"
    failure_mode_identifier: Mapped[str] = mapped_column(String(120), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (
        UniqueConstraint("tenant_id", "failure_mode_identifier", name="uq_failure_modes_tenant_identifier"),
        UniqueConstraint("tenant_id", "id", name="uq_failure_modes_tenant_id_id"),
    )


class Control(TenantOwned, Base):
    __tablename__ = "controls"
    control_identifier: Mapped[str] = mapped_column(String(120), nullable=False)
    control_type: Mapped[str | None] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, server_default="active")
    __table_args__ = (
        UniqueConstraint("tenant_id", "control_identifier", name="uq_controls_tenant_identifier"),
        UniqueConstraint("tenant_id", "id", name="uq_controls_tenant_id_id"),
    )


class Evidence(TenantOwned, Base):
    __tablename__ = "evidence"
    evidence_identifier: Mapped[str] = mapped_column(String(120), nullable=False)
    investigation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    evidence_type: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_reference: Mapped[str | None] = mapped_column(Text)
    document_ref: Mapped[str | None] = mapped_column(Text)
    extracted_text_ref: Mapped[str | None] = mapped_column(Text)
    reliability_status: Mapped[str] = mapped_column(String(40), nullable=False, server_default="unreviewed")
    fact_type: Mapped[str] = mapped_column(String(40), nullable=False, server_default="source_fact")
    content: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (
        ForeignKeyConstraint(["tenant_id", "investigation_id"], ["investigations.tenant_id", "investigations.id"]),
        CheckConstraint("fact_type in ('source_fact','derived_fact','ai_inference')", name="evidence_fact_type_allowed"),
        UniqueConstraint("tenant_id", "evidence_identifier", name="uq_evidence_tenant_identifier"),
        UniqueConstraint("tenant_id", "id", name="uq_evidence_tenant_id_id"),
    )


class Hypothesis(TenantOwned, Base):
    __tablename__ = "hypotheses"
    investigation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, server_default="proposed")
    origin: Mapped[str] = mapped_column(String(20), nullable=False)
    reviewer_disposition: Mapped[str | None] = mapped_column(String(80))
    __table_args__ = (
        ForeignKeyConstraint(["tenant_id", "investigation_id"], ["investigations.tenant_id", "investigations.id"]),
        CheckConstraint("origin in ('ai','human','system')", name="hypothesis_origin_allowed"),
        UniqueConstraint("tenant_id", "id", name="uq_hypotheses_tenant_id_id"),
    )


class Unknown(Base):
    __tablename__ = "unknowns"
    id = uuid_pk()
    tenant_id = tenant_fk()
    investigation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    hypothesis_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    category: Mapped[str | None] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_needed: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), nullable=False, server_default="open")
    resolution: Mapped[str | None] = mapped_column(Text)
    created_at = tz(False)
    updated_at = tz(False)
    __table_args__ = (
        ForeignKeyConstraint(["tenant_id", "investigation_id"], ["investigations.tenant_id", "investigations.id"]),
        ForeignKeyConstraint(["tenant_id", "hypothesis_id"], ["hypotheses.tenant_id", "hypotheses.id"]),
        UniqueConstraint("tenant_id", "id", name="uq_unknowns_tenant_id_id"),
    )


class FailureChain(Base):
    __tablename__ = "failure_chains"
    id = uuid_pk()
    tenant_id = tenant_fk()
    investigation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, server_default="draft")
    created_at = tz(False)
    updated_at = tz(False)
    __table_args__ = (
        ForeignKeyConstraint(["tenant_id", "investigation_id"], ["investigations.tenant_id", "investigations.id"]),
        UniqueConstraint("tenant_id", "id", name="uq_failure_chains_tenant_id_id"),
    )


class Scenario(TenantOwned, Base):
    __tablename__ = "scenarios"
    investigation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    scenario_identifier: Mapped[str] = mapped_column(String(120), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    assumptions: Mapped[dict | None] = mapped_column(JSONB)
    uncertainty: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), nullable=False, server_default="draft")
    __table_args__ = (
        ForeignKeyConstraint(["tenant_id", "investigation_id"], ["investigations.tenant_id", "investigations.id"]),
        UniqueConstraint("tenant_id", "scenario_identifier", name="uq_scenarios_tenant_identifier"),
        UniqueConstraint("tenant_id", "id", name="uq_scenarios_tenant_id_id"),
    )


class AIExecution(Base):
    __tablename__ = "ai_executions"
    id = uuid_pk()
    tenant_id = tenant_fk()
    investigation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    requestor_ref: Mapped[str | None] = mapped_column(String(255))
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    model_name: Mapped[str] = mapped_column(String(120), nullable=False)
    model_version: Mapped[str | None] = mapped_column(String(120))
    prompt_template_version: Mapped[str | None] = mapped_column(String(120))
    orchestration_version: Mapped[str | None] = mapped_column(String(120))
    context_refs: Mapped[dict | None] = mapped_column(JSONB)
    evidence_refs: Mapped[dict | None] = mapped_column(JSONB)
    tools_invoked: Mapped[dict | None] = mapped_column(JSONB)
    structured_input: Mapped[dict | None] = mapped_column(JSONB)
    structured_output: Mapped[dict | None] = mapped_column(JSONB)
    rationale_summary: Mapped[str | None] = mapped_column(Text)
    confidence_label: Mapped[str | None] = mapped_column(String(80))
    validation_status: Mapped[str | None] = mapped_column(String(80))
    execution_timestamp = tz(False)
    latency_ms: Mapped[int | None] = mapped_column()
    error_state: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (
        ForeignKeyConstraint(["tenant_id", "investigation_id"], ["investigations.tenant_id", "investigations.id"]),
        UniqueConstraint("tenant_id", "id", name="uq_ai_executions_tenant_id_id"),
    )


class Decision(Base):
    __tablename__ = "decisions"
    id = uuid_pk()
    tenant_id = tenant_fk()
    investigation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    decision_identifier: Mapped[str] = mapped_column(String(120), nullable=False)
    decision_type: Mapped[str] = mapped_column(String(80), nullable=False)
    disposition: Mapped[str] = mapped_column(String(80), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    product_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    product_version_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    decision_status: Mapped[str] = mapped_column(String(50), nullable=False, server_default="DRAFT")
    decision_readiness: Mapped[str | None] = mapped_column(String(80))
    selected_action: Mapped[str | None] = mapped_column(String(120))
    human_decision: Mapped[str | None] = mapped_column(Text)
    limitations: Mapped[dict | None] = mapped_column(JSONB)
    temporal_context: Mapped[dict | None] = mapped_column(JSONB)
    context_snapshot: Mapped[dict | None] = mapped_column(JSONB)
    advisory_execution_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    updated_at = tz(False)
    decision_timestamp = tz(False)
    authorized_by_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at = tz(False)
    __table_args__ = (
        ForeignKeyConstraint(["tenant_id", "investigation_id"], ["investigations.tenant_id", "investigations.id"]),
        UniqueConstraint("tenant_id", "decision_identifier", name="uq_decisions_tenant_identifier"),
        UniqueConstraint("tenant_id", "id", name="uq_decisions_tenant_id_id"),
    )


class HumanReview(Base):
    __tablename__ = "human_reviews"
    id = uuid_pk()
    tenant_id = tenant_fk()
    investigation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    ai_execution_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    decision_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    reviewer_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    disposition: Mapped[str] = mapped_column(String(80), nullable=False)
    comments: Mapped[str | None] = mapped_column(Text)
    review_timestamp = tz(False)
    __table_args__ = (
        ForeignKeyConstraint(["tenant_id", "investigation_id"], ["investigations.tenant_id", "investigations.id"]),
        ForeignKeyConstraint(["tenant_id", "ai_execution_id"], ["ai_executions.tenant_id", "ai_executions.id"]),
        ForeignKeyConstraint(["tenant_id", "decision_id"], ["decisions.tenant_id", "decisions.id"]),
        UniqueConstraint("tenant_id", "id", name="uq_human_reviews_tenant_id_id"),
    )


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id = uuid_pk()
    tenant_id = tenant_fk()
    actor_ref: Mapped[str | None] = mapped_column(String(255))
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    correlation_id: Mapped[str | None] = mapped_column(String(120))
    details: Mapped[dict | None] = mapped_column(JSONB)
    source_ip: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str | None] = mapped_column(String(512))
    reason: Mapped[str | None] = mapped_column(Text)
    old_values: Mapped[dict | None] = mapped_column(JSONB)
    new_values: Mapped[dict | None] = mapped_column(JSONB)
    retention_until = tz(True)
    created_at = tz(False)


class InvestigationBrief(Base):
    """Immutable, versioned investigation brief snapshot."""
    __tablename__ = "investigation_briefs"
    id = uuid_pk()
    tenant_id = tenant_fk()
    investigation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    product_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    product_version_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    brief_version: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, server_default="GENERATED")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    generated_by: Mapped[str] = mapped_column(String(255), nullable=False)
    temporal_mode: Mapped[str] = mapped_column(String(20), nullable=False)
    temporal_cutoff = tz(True)
    ai_execution_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    human_review_state: Mapped[str] = mapped_column(String(40), nullable=False, server_default="NOT_REVIEWED")
    decision_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    limitations: Mapped[dict | None] = mapped_column(JSONB)
    content: Mapped[dict] = mapped_column(JSONB, nullable=False)
    provenance: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at = tz(False)
    updated_at = tz(False)
    __table_args__ = (
        ForeignKeyConstraint(["tenant_id", "investigation_id"], ["investigations.tenant_id", "investigations.id"]),
        UniqueConstraint("tenant_id", "investigation_id", "brief_version", name="uq_briefs_tenant_investigation_version"),
        UniqueConstraint("tenant_id", "id", name="uq_briefs_tenant_id_id"),
    )

class AssuranceResult(Base):
    __tablename__ = "assurance_results"
    id = uuid_pk(); tenant_id = tenant_fk()
    investigation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    ai_execution_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    output_type: Mapped[str] = mapped_column(String(80), nullable=False)
    output_id: Mapped[str | None] = mapped_column(String(255))
    assurance_version: Mapped[int] = mapped_column(nullable=False, server_default="1")
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    generated_at = tz(False); trust_policy_version: Mapped[str] = mapped_column(String(120), nullable=False)
    product_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True)); product_version_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    temporal_mode: Mapped[str | None] = mapped_column(String(20)); temporal_cutoff = tz(True)
    human_review_required: Mapped[bool] = mapped_column(nullable=False, server_default="true")
    revalidation_required: Mapped[bool] = mapped_column(nullable=False, server_default="false")
    limitations: Mapped[dict | None] = mapped_column(JSONB); configuration_hash: Mapped[str | None] = mapped_column(String(64))
    created_at = tz(False)
    __table_args__ = (ForeignKeyConstraint(["tenant_id", "ai_execution_id"], ["ai_executions.tenant_id", "ai_executions.id"]), UniqueConstraint("tenant_id", "id", name="uq_assurance_results_tenant_id_id"))

class AssuranceCheck(Base):
    __tablename__ = "assurance_checks"
    id = uuid_pk(); tenant_id = tenant_fk(); assurance_result_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    check_type: Mapped[str] = mapped_column(String(80), nullable=False); status: Mapped[str] = mapped_column(String(40), nullable=False); severity: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False); evidence_reference: Mapped[dict | None] = mapped_column(JSONB); details: Mapped[dict | None] = mapped_column(JSONB); created_at = tz(False)
    __table_args__ = (ForeignKeyConstraint(["tenant_id", "assurance_result_id"], ["assurance_results.tenant_id", "assurance_results.id"]), UniqueConstraint("tenant_id", "id", name="uq_assurance_checks_tenant_id_id"))

class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"
    id = uuid_pk(); tenant_id = tenant_fk(); suite_version: Mapped[str] = mapped_column(String(120), nullable=False); dataset_version: Mapped[str] = mapped_column(String(120), nullable=False); release_version: Mapped[str] = mapped_column(String(120), nullable=False); configuration_hash: Mapped[str] = mapped_column(String(64), nullable=False); status: Mapped[str] = mapped_column(String(40), nullable=False); results: Mapped[dict] = mapped_column(JSONB, nullable=False); started_at = tz(False); completed_at = tz(False); created_at = tz(False)
    __table_args__ = (UniqueConstraint("tenant_id", "id", name="uq_evaluation_runs_tenant_id_id"),)

class ReleaseAssuranceResult(Base):
    __tablename__ = "release_assurance_results"
    id = uuid_pk(); tenant_id = tenant_fk(); evaluation_run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False); release_version: Mapped[str] = mapped_column(String(120), nullable=False); suite_version: Mapped[str] = mapped_column(String(120), nullable=False); dataset_version: Mapped[str] = mapped_column(String(120), nullable=False); configuration_hash: Mapped[str] = mapped_column(String(64), nullable=False); status: Mapped[str] = mapped_column(String(40), nullable=False); critical_failures: Mapped[dict | None] = mapped_column(JSONB); limitations: Mapped[dict | None] = mapped_column(JSONB); revalidation_required: Mapped[bool] = mapped_column(nullable=False, server_default="false"); review_status: Mapped[str] = mapped_column(String(40), nullable=False, server_default="REQUIRES_HUMAN_REVIEW"); generated_at = tz(False); created_at = tz(False)
    __table_args__ = (ForeignKeyConstraint(["tenant_id", "evaluation_run_id"], ["evaluation_runs.tenant_id", "evaluation_runs.id"]), UniqueConstraint("tenant_id", "id", name="uq_release_assurance_tenant_id_id"),)

class AuthUser(Base):
    __tablename__ = "auth_users"
    id = uuid_pk(); tenant_id = tenant_fk(); username: Mapped[str] = mapped_column(String(254), nullable=False); display_name: Mapped[str] = mapped_column(String(120), nullable=False); company: Mapped[str] = mapped_column(String(160), nullable=False); password_hash: Mapped[str] = mapped_column(Text, nullable=False); role: Mapped[str] = mapped_column(String(120), nullable=False, server_default="Viewer"); status: Mapped[str] = mapped_column(String(40), nullable=False, server_default="PENDING_VERIFICATION"); email_verified: Mapped[bool] = mapped_column(nullable=False, server_default="false"); mfa_required: Mapped[bool] = mapped_column(nullable=False, server_default="false"); mfa_enrolled_at = tz(True); password_changed_at = tz(True); password_expires_at = tz(True); created_at = tz(False); updated_at = tz(False)
    __table_args__ = (UniqueConstraint("tenant_id", "username", name="uq_auth_users_tenant_username"), UniqueConstraint("tenant_id", "id", name="uq_auth_users_tenant_id_id"),)

class TenantMembership(Base):
    __tablename__ = "tenant_memberships"
    id = uuid_pk(); tenant_id = tenant_fk(); user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False); status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="ACTIVE"); is_default: Mapped[bool] = mapped_column(nullable=False, server_default="false"); created_at = tz(False); updated_at = tz(False)
    __table_args__ = (ForeignKeyConstraint(["tenant_id", "user_id"], ["auth_users.tenant_id", "auth_users.id"]), UniqueConstraint("tenant_id", "user_id", name="uq_tenant_membership"), UniqueConstraint("tenant_id", "id", name="uq_tenant_membership_tenant_id"))

class PersonaAssignment(Base):
    __tablename__ = "persona_assignments"
    id = uuid_pk(); tenant_id = tenant_fk(); user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False); persona_code: Mapped[str] = mapped_column(String(80), nullable=False); status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="ACTIVE"); created_at = tz(False); updated_at = tz(False)
    __table_args__ = (ForeignKeyConstraint(["tenant_id", "user_id"], ["auth_users.tenant_id", "auth_users.id"]), UniqueConstraint("tenant_id", "user_id", "persona_code", name="uq_persona_assignment"), UniqueConstraint("tenant_id", "id", name="uq_persona_assignment_tenant_id"))

class PermissionSetDefinition(Base):
    __tablename__ = "permission_set_definitions"
    id = uuid_pk(); tenant_id = tenant_fk(); code: Mapped[str] = mapped_column(String(100), nullable=False); object_permissions: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}"); field_permissions: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}"); action_permissions: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}"); version: Mapped[str] = mapped_column(String(40), nullable=False, server_default="v1"); status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="DRAFT"); created_at = tz(False); updated_at = tz(False)
    __table_args__ = (UniqueConstraint("tenant_id", "code", "version", name="uq_permission_set_definition"), UniqueConstraint("tenant_id", "id", name="uq_permission_set_definition_tenant_id"))

class RoleDefinition(Base):
    __tablename__ = "role_definitions"
    id = uuid_pk(); tenant_id = tenant_fk(); code: Mapped[str] = mapped_column(String(100), nullable=False); name: Mapped[str] = mapped_column(String(120), nullable=False); version: Mapped[str] = mapped_column(String(40), nullable=False, server_default="v1"); status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="DRAFT"); created_at = tz(False); updated_at = tz(False)
    __table_args__ = (UniqueConstraint("tenant_id", "code", "version", name="uq_role_definition"), UniqueConstraint("tenant_id", "id", name="uq_role_definition_tenant_id"))

class RolePermissionSet(Base):
    __tablename__ = "role_permission_sets"
    id = uuid_pk(); tenant_id = tenant_fk(); role_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False); permission_set_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False); created_at = tz(False)
    __table_args__ = (ForeignKeyConstraint(["tenant_id", "role_id"], ["role_definitions.tenant_id", "role_definitions.id"]), ForeignKeyConstraint(["tenant_id", "permission_set_id"], ["permission_set_definitions.tenant_id", "permission_set_definitions.id"]), UniqueConstraint("tenant_id", "role_id", "permission_set_id", name="uq_role_permission_set"))

class RoleAssignment(Base):
    __tablename__ = "role_assignments"
    id = uuid_pk(); tenant_id = tenant_fk(); user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False); role_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False); status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="ACTIVE"); created_at = tz(False); updated_at = tz(False)
    __table_args__ = (ForeignKeyConstraint(["tenant_id", "user_id"], ["auth_users.tenant_id", "auth_users.id"]), ForeignKeyConstraint(["tenant_id", "role_id"], ["role_definitions.tenant_id", "role_definitions.id"]), UniqueConstraint("tenant_id", "user_id", "role_id", name="uq_role_assignment"), UniqueConstraint("tenant_id", "id", name="uq_role_assignment_tenant_id"))


class PlanDefinition(Base):
    __tablename__ = "plan_definitions"
    id = uuid_pk(); code: Mapped[str] = mapped_column(String(80), nullable=False, unique=True); name: Mapped[str] = mapped_column(String(120), nullable=False); description: Mapped[str | None] = mapped_column(Text); version: Mapped[str] = mapped_column(String(40), nullable=False); status: Mapped[str] = mapped_column(String(30), nullable=False); effective_from = tz(False); effective_to = tz(); created_at = tz(False); updated_at = tz(False)

class FeatureEntitlement(Base):
    __tablename__ = "feature_entitlements"
    id = uuid_pk(); plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("plan_definitions.id"), nullable=False); feature_code: Mapped[str] = mapped_column(String(120), nullable=False); enabled: Mapped[bool] = mapped_column(nullable=False); limits: Mapped[dict | None] = mapped_column(JSONB); status: Mapped[str] = mapped_column(String(30), nullable=False); created_at = tz(False); updated_at = tz(False)
    __table_args__ = (UniqueConstraint("plan_id", "feature_code", name="uq_plan_feature_entitlement"),)

class TenantPlanAssignment(Base):
    __tablename__ = "tenant_plan_assignments"
    id = uuid_pk(); tenant_id = tenant_fk(); plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("plan_definitions.id"), nullable=False); status: Mapped[str] = mapped_column(String(30), nullable=False); effective_from = tz(False); effective_to = tz(); reason: Mapped[str | None] = mapped_column(Text); created_at = tz(False); updated_at = tz(False)

class ApprovalAuthority(Base):
    __tablename__ = "approval_authorities"
    id = uuid_pk(); tenant_id = tenant_fk(); role_name: Mapped[str] = mapped_column(String(120), nullable=False); object_type: Mapped[str] = mapped_column(String(120), nullable=False); decision_type: Mapped[str] = mapped_column(String(120), nullable=False); scope: Mapped[dict | None] = mapped_column(JSONB); authority: Mapped[str] = mapped_column(String(30), nullable=False); version: Mapped[str] = mapped_column(String(40), nullable=False); status: Mapped[str] = mapped_column(String(30), nullable=False); effective_from = tz(False); effective_to = tz(); created_at = tz(False); updated_at = tz(False)

class SegregationOfDutiesPolicy(Base):
    __tablename__ = "segregation_of_duties_policies"
    id = uuid_pk(); tenant_id = tenant_fk(); name: Mapped[str] = mapped_column(String(160), nullable=False); object_type: Mapped[str] = mapped_column(String(120), nullable=False); decision_type: Mapped[str] = mapped_column(String(120), nullable=False); creator_cannot_approve: Mapped[bool] = mapped_column(nullable=False); last_material_editor_cannot_approve: Mapped[bool] = mapped_column(nullable=False); version: Mapped[str] = mapped_column(String(40), nullable=False); status: Mapped[str] = mapped_column(String(30), nullable=False); effective_from = tz(False); effective_to = tz(); created_at = tz(False); updated_at = tz(False)

class SignedApprovalRecord(Base):
    __tablename__ = "signed_approval_records"
    id = uuid_pk(); tenant_id = tenant_fk(); object_type: Mapped[str] = mapped_column(String(120), nullable=False); object_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False); object_version: Mapped[str] = mapped_column(String(80), nullable=False); decision_type: Mapped[str] = mapped_column(String(120), nullable=False); decision: Mapped[str] = mapped_column(String(12), nullable=False); remarks: Mapped[str] = mapped_column(Text, nullable=False); signer_user_id: Mapped[str] = mapped_column(String(254), nullable=False); signer_role: Mapped[str] = mapped_column(String(120), nullable=False); signature_meaning: Mapped[str] = mapped_column(Text, nullable=False); content_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False); signature_hash: Mapped[str] = mapped_column(String(64), nullable=False); status: Mapped[str] = mapped_column(String(30), nullable=False); signed_at = tz(False); invalidated_at = tz(); invalidation_reason: Mapped[str | None] = mapped_column(Text); created_at = tz(False)
    __table_args__ = (UniqueConstraint("tenant_id", "object_type", "object_id", "object_version", "decision_type", name="uq_signed_approval_version"),)


class ProductComponent(Base):
    __tablename__ = "product_components"
    id = uuid_pk()
    tenant_id = tenant_fk()
    product_version_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    component_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    relationship_status: Mapped[str] = mapped_column(String(40), nullable=False, server_default="active")
    effective_timestamp = tz()
    evidence_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at = tz(False)
    __table_args__ = (
        ForeignKeyConstraint(["tenant_id", "product_version_id"], ["product_versions.tenant_id", "product_versions.id"]),
        ForeignKeyConstraint(["tenant_id", "component_id"], ["components.tenant_id", "components.id"]),
        ForeignKeyConstraint(["tenant_id", "evidence_id"], ["evidence.tenant_id", "evidence.id"]),
        UniqueConstraint("tenant_id", "product_version_id", "component_id", name="uq_product_components_version_component"),
    )


class ProductSupplier(Base):
    __tablename__ = "product_suppliers"
    id = uuid_pk()
    tenant_id = tenant_fk()
    product_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    effective_timestamp = tz()
    evidence_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at = tz(False)
    __table_args__ = (
        ForeignKeyConstraint(["tenant_id", "product_id"], ["products.tenant_id", "products.id"]),
        ForeignKeyConstraint(["tenant_id", "supplier_id"], ["suppliers.tenant_id", "suppliers.id"]),
        ForeignKeyConstraint(["tenant_id", "evidence_id"], ["evidence.tenant_id", "evidence.id"]),
    )


class ComponentSupplier(Base):
    __tablename__ = "component_suppliers"
    id = uuid_pk()
    tenant_id = tenant_fk()
    component_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    supplier_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    effective_timestamp = tz()
    evidence_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at = tz(False)
    __table_args__ = (
        ForeignKeyConstraint(["tenant_id", "component_id"], ["components.tenant_id", "components.id"]),
        ForeignKeyConstraint(["tenant_id", "supplier_id"], ["suppliers.tenant_id", "suppliers.id"]),
        ForeignKeyConstraint(["tenant_id", "evidence_id"], ["evidence.tenant_id", "evidence.id"]),
        UniqueConstraint("tenant_id", "component_id", "supplier_id", name="uq_component_suppliers_component_supplier"),
    )


class LotComponent(Base):
    __tablename__ = "lot_components"
    id = uuid_pk()
    tenant_id = tenant_fk()
    lot_batch_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    component_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    evidence_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at = tz(False)
    __table_args__ = (
        ForeignKeyConstraint(["tenant_id", "lot_batch_id"], ["lot_batches.tenant_id", "lot_batches.id"]),
        ForeignKeyConstraint(["tenant_id", "component_id"], ["components.tenant_id", "components.id"]),
        ForeignKeyConstraint(["tenant_id", "evidence_id"], ["evidence.tenant_id", "evidence.id"]),
    )


class InvestigationComplaint(Base):
    __tablename__ = "investigation_complaints"
    id = uuid_pk()
    tenant_id = tenant_fk()
    investigation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    complaint_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at = tz(False)
    __table_args__ = (
        ForeignKeyConstraint(["tenant_id", "investigation_id"], ["investigations.tenant_id", "investigations.id"]),
        ForeignKeyConstraint(["tenant_id", "complaint_id"], ["complaints.tenant_id", "complaints.id"]),
        UniqueConstraint("tenant_id", "investigation_id", "complaint_id", name="uq_investigation_complaints_pair"),
    )


class InvestigationEvidence(Base):
    __tablename__ = "investigation_evidence"
    id = uuid_pk()
    tenant_id = tenant_fk()
    investigation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    evidence_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    relevance: Mapped[str | None] = mapped_column(Text)
    created_at = tz(False)
    __table_args__ = (
        ForeignKeyConstraint(["tenant_id", "investigation_id"], ["investigations.tenant_id", "investigations.id"]),
        ForeignKeyConstraint(["tenant_id", "evidence_id"], ["evidence.tenant_id", "evidence.id"]),
        UniqueConstraint("tenant_id", "investigation_id", "evidence_id", name="uq_investigation_evidence_pair"),
    )


class HypothesisEvidence(Base):
    __tablename__ = "hypothesis_evidence"
    id = uuid_pk()
    tenant_id = tenant_fk()
    hypothesis_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    evidence_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    relation_type: Mapped[str] = mapped_column(String(20), nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text)
    created_by_type: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at = tz(False)
    __table_args__ = (
        ForeignKeyConstraint(["tenant_id", "hypothesis_id"], ["hypotheses.tenant_id", "hypotheses.id"]),
        ForeignKeyConstraint(["tenant_id", "evidence_id"], ["evidence.tenant_id", "evidence.id"]),
        CheckConstraint("relation_type in ('support','contradict')", name="hypothesis_evidence_relation_allowed"),
        CheckConstraint("created_by_type in ('ai','human','system')", name="hypothesis_evidence_creator_allowed"),
    )


class FailureChainNode(Base):
    __tablename__ = "failure_chain_nodes"
    id = uuid_pk()
    tenant_id = tenant_fk()
    failure_chain_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    sequence_number: Mapped[int] = mapped_column(nullable=False)
    node_type: Mapped[str] = mapped_column(String(80), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    lifecycle_object_type: Mapped[str | None] = mapped_column(String(120))
    lifecycle_object_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    evidence_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at = tz(False)
    __table_args__ = (
        ForeignKeyConstraint(["tenant_id", "failure_chain_id"], ["failure_chains.tenant_id", "failure_chains.id"]),
        ForeignKeyConstraint(["tenant_id", "evidence_id"], ["evidence.tenant_id", "evidence.id"]),
        UniqueConstraint("tenant_id", "failure_chain_id", "sequence_number", name="uq_failure_chain_nodes_sequence"),
        UniqueConstraint("tenant_id", "id", name="uq_failure_chain_nodes_tenant_id_id"),
    )


class FailureChainEdge(Base):
    __tablename__ = "failure_chain_edges"
    id = uuid_pk()
    tenant_id = tenant_fk()
    failure_chain_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    from_node_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    to_node_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    edge_status: Mapped[str] = mapped_column(String(40), nullable=False)
    evidence_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    rationale: Mapped[str | None] = mapped_column(Text)
    created_at = tz(False)
    __table_args__ = (
        ForeignKeyConstraint(["tenant_id", "failure_chain_id"], ["failure_chains.tenant_id", "failure_chains.id"]),
        ForeignKeyConstraint(["tenant_id", "from_node_id"], ["failure_chain_nodes.tenant_id", "failure_chain_nodes.id"], name="fk_failure_chain_edges_from_node"),
        ForeignKeyConstraint(["tenant_id", "to_node_id"], ["failure_chain_nodes.tenant_id", "failure_chain_nodes.id"], name="fk_failure_chain_edges_to_node"),
        ForeignKeyConstraint(["tenant_id", "evidence_id"], ["evidence.tenant_id", "evidence.id"]),
        CheckConstraint("edge_status in ('established_fact','hypothesized','contradicted')", name="failure_chain_edge_status_allowed"),
    )


class RealityRelationship(Base):
    __tablename__ = "reality_relationships"
    id = uuid_pk()
    tenant_id = tenant_fk()
    source_entity_type: Mapped[str] = mapped_column(String(120), nullable=False)
    source_entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    target_entity_type: Mapped[str] = mapped_column(String(120), nullable=False)
    target_entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(120), nullable=False)
    assertion_status: Mapped[str] = mapped_column(String(40), nullable=False, server_default="supported")
    evidence_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    confidence_label: Mapped[str | None] = mapped_column(String(80))
    effective_timestamp = tz()
    recorded_timestamp = tz()
    provenance: Mapped[dict | None] = mapped_column(JSONB)
    created_at = tz(False)
    __table_args__ = (
        ForeignKeyConstraint(["tenant_id", "evidence_id"], ["evidence.tenant_id", "evidence.id"]),
        CheckConstraint("assertion_status in ('supported','contradicted','hypothesized','unknown')", name="reality_relationship_assertion_allowed"),
    )


class EvidenceEmbedding(Base):
    __tablename__ = "evidence_embeddings"
    id = uuid_pk()
    tenant_id = tenant_fk()
    evidence_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(120), nullable=False)
    embedding: Mapped[object | None] = mapped_column(Vector(1536))
    embedding_vector_ref: Mapped[str | None] = mapped_column(String(255))
    created_at = tz(False)
    __table_args__ = (
        ForeignKeyConstraint(["tenant_id", "evidence_id"], ["evidence.tenant_id", "evidence.id"]),
    )


class ConnectorConfiguration(Base):
    __tablename__ = "connector_configurations"
    id = uuid_pk(); tenant_id = tenant_fk()
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    connector_type: Mapped[str] = mapped_column(String(80), nullable=False)
    configuration: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    version: Mapped[str] = mapped_column(String(40), nullable=False, server_default="v1")
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="DRAFT")
    created_at = tz(False); updated_at = tz(False)
    __table_args__ = (UniqueConstraint("tenant_id", "code", "version", name="uq_connector_configuration"),)


class MappingConfiguration(Base):
    __tablename__ = "mapping_configurations"
    id = uuid_pk(); tenant_id = tenant_fk()
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    source_system: Mapped[str] = mapped_column(String(120), nullable=False)
    target_entity: Mapped[str] = mapped_column(String(120), nullable=False)
    mapping_rules: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}")
    version: Mapped[str] = mapped_column(String(40), nullable=False, server_default="v1")
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="DRAFT")
    created_at = tz(False); updated_at = tz(False)
    __table_args__ = (UniqueConstraint("tenant_id", "code", "version", name="uq_mapping_configuration"),)


class MasterMapping(Base):
    __tablename__ = "master_mappings"
    id = uuid_pk(); code: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    source_system: Mapped[str] = mapped_column(String(120), nullable=False); target_entity: Mapped[str] = mapped_column(String(120), nullable=False)
    definition: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}"); status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="ACTIVE")
    created_at = tz(False); updated_at = tz(False)


class TenantMappingVersion(Base):
    __tablename__ = "tenant_mapping_versions"
    id = uuid_pk(); tenant_id = tenant_fk(); master_mapping_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    version: Mapped[str] = mapped_column(String(40), nullable=False); rules: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}"); status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="DRAFT")
    effective_from = tz(); effective_to = tz(); created_at = tz(False); updated_at = tz(False)
    __table_args__ = (ForeignKeyConstraint(["tenant_id"], ["tenants.id"]), ForeignKeyConstraint(["master_mapping_id"], ["master_mappings.id"]), UniqueConstraint("tenant_id", "master_mapping_id", "version", name="uq_tenant_mapping_version"), UniqueConstraint("tenant_id", "id", name="uq_tenant_mapping_version_tenant_id"))


class TenantMappingOverride(Base):
    __tablename__ = "tenant_mapping_overrides"
    id = uuid_pk(); tenant_id = tenant_fk(); mapping_version_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    field_name: Mapped[str] = mapped_column(String(160), nullable=False); override_rule: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}"); status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="ACTIVE")
    created_at = tz(False); updated_at = tz(False)
    __table_args__ = (ForeignKeyConstraint(["tenant_id", "mapping_version_id"], ["tenant_mapping_versions.tenant_id", "tenant_mapping_versions.id"]), UniqueConstraint("tenant_id", "mapping_version_id", "field_name", name="uq_tenant_mapping_override"))

class MappingImpactHistory(Base):
    __tablename__ = "mapping_impact_history"
    id = uuid_pk(); tenant_id = tenant_fk(); master_mapping_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    from_version: Mapped[str | None] = mapped_column(String(40)); to_version: Mapped[str] = mapped_column(String(40), nullable=False)
    impact: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="{}"); created_at = tz(False)
    __table_args__ = (ForeignKeyConstraint(["tenant_id"], ["tenants.id"]), ForeignKeyConstraint(["master_mapping_id"], ["master_mappings.id"]))


Index("ix_products_tenant_product_identifier", Product.tenant_id, Product.product_identifier)
Index("ix_product_versions_tenant_product", ProductVersion.tenant_id, ProductVersion.product_id)
Index("ix_components_tenant_identifier", Component.tenant_id, Component.component_identifier)
Index("ix_complaints_tenant_product_event", Complaint.tenant_id, Complaint.product_id, Complaint.event_timestamp)
Index("ix_investigations_tenant_product", Investigation.tenant_id, Investigation.product_id)
Index("ix_evidence_tenant_investigation", Evidence.tenant_id, Evidence.investigation_id)
Index("ix_hypothesis_evidence_relation", HypothesisEvidence.tenant_id, HypothesisEvidence.hypothesis_id, HypothesisEvidence.relation_type)
Index("ix_reality_relationship_lookup", RealityRelationship.tenant_id, RealityRelationship.source_entity_type, RealityRelationship.source_entity_id)
