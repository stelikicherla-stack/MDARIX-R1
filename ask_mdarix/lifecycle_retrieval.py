"""Bounded, tenant-authorized Day 28 lifecycle neighborhood retrieval."""
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.ai_boundary import build_context
from backend.app.db.models.foundation import (
    Change, Complaint, Component, ComponentSupplier, Control, Evidence,
    FailureMode, Investigation, InvestigationComplaint, InvestigationEvidence,
    LotBatch, LotComponent, Product, ProductComponent, ProductVersion,
    Requirement, Risk, Supplier, ManufacturingSite,
)


@dataclass(frozen=True)
class LifecycleRetrievalRequest:
    tenant_id: UUID
    product_id: UUID | None = None
    product_version_id: UUID | None = None
    complaint_id: UUID | None = None
    investigation_id: UUID | None = None
    evidence_id: UUID | None = None
    limit: int = 25


def _safe(row: Any, fields: tuple[str, ...]) -> dict[str, Any]:
    result: dict[str, Any] = {"id": str(row.id)}
    for field in fields:
        value = getattr(row, field, None)
        result[field] = str(value) if isinstance(value, UUID) else value
    return result


class LifecycleRetrievalService:
    def retrieve(self, db: Session, request: LifecycleRetrievalRequest) -> dict[str, Any]:
        limit = max(1, min(request.limit, 100))
        tenant = request.tenant_id
        products: list[Product] = []
        versions: list[ProductVersion] = []

        if request.product_id:
            products = db.query(Product).filter(Product.tenant_id == tenant, Product.id == request.product_id).limit(limit).all()
        if request.product_version_id:
            versions = db.query(ProductVersion).filter(ProductVersion.tenant_id == tenant, ProductVersion.id == request.product_version_id).limit(limit).all()
        if request.product_id:
            versions = db.query(ProductVersion).filter(ProductVersion.tenant_id == tenant, ProductVersion.product_id == request.product_id).limit(limit).all() if not request.product_version_id else versions
        if versions and not products:
            products = db.query(Product).filter(Product.tenant_id == tenant, Product.id.in_({row.product_id for row in versions})).limit(limit).all()
        product_ids = {row.id for row in products}
        version_ids = {row.id for row in versions}
        if request.product_version_id and versions and request.product_id and versions[0].product_id != request.product_id:
            versions = []
            version_ids = set()

        investigations: list[Investigation] = []
        complaints: list[Complaint] = []
        evidence: list[Evidence] = []
        if request.investigation_id:
            investigations = db.query(Investigation).filter(Investigation.tenant_id == tenant, Investigation.id == request.investigation_id).limit(limit).all()
        if request.complaint_id:
            complaints = db.query(Complaint).filter(Complaint.tenant_id == tenant, Complaint.id == request.complaint_id).limit(limit).all()
        if request.evidence_id:
            evidence = db.query(Evidence).filter(Evidence.tenant_id == tenant, Evidence.id == request.evidence_id).limit(limit).all()

        investigation_ids = {row.id for row in investigations}
        if complaints:
            investigation_ids.update(row.id for row in db.query(Investigation).join(InvestigationComplaint, InvestigationComplaint.investigation_id == Investigation.id).filter(Investigation.tenant_id == tenant, InvestigationComplaint.tenant_id == tenant, InvestigationComplaint.complaint_id.in_([row.id for row in complaints])).limit(limit).all())
        if investigation_ids:
            evidence_ids = [row.evidence_id for row in db.query(InvestigationEvidence).filter(InvestigationEvidence.tenant_id == tenant, InvestigationEvidence.investigation_id.in_(investigation_ids)).limit(limit).all()]
            if evidence_ids and not evidence:
                evidence = db.query(Evidence).filter(Evidence.tenant_id == tenant, Evidence.id.in_(evidence_ids)).limit(limit).all()

        components = db.query(Component).join(ProductComponent, ProductComponent.component_id == Component.id).filter(Component.tenant_id == tenant, ProductComponent.tenant_id == tenant, ProductComponent.product_version_id.in_(version_ids)).limit(limit).all() if version_ids else []
        component_ids = {row.id for row in components}
        suppliers = db.query(Supplier).join(ComponentSupplier, ComponentSupplier.supplier_id == Supplier.id).filter(Supplier.tenant_id == tenant, ComponentSupplier.tenant_id == tenant, ComponentSupplier.component_id.in_(component_ids)).limit(limit).all() if component_ids else []
        supplier_ids = {row.id for row in suppliers}
        sites: list[ManufacturingSite] = []
        lots = db.query(LotBatch).filter(LotBatch.tenant_id == tenant, LotBatch.product_version_id.in_(version_ids)).limit(limit).all() if version_ids else []
        requirements = db.query(Requirement).filter(Requirement.tenant_id == tenant, Requirement.product_version_id.in_(version_ids)).limit(limit).all() if version_ids else []
        changes: list[Change] = []
        risks = db.query(Risk).filter(Risk.tenant_id == tenant, Risk.product_version_id.in_(version_ids)).limit(limit).all() if version_ids else []
        failure_modes: list[FailureMode] = []
        controls: list[Control] = []

        relationships: list[dict[str, Any]] = []
        component_links = db.query(ProductComponent).filter(ProductComponent.tenant_id == tenant, ProductComponent.product_version_id.in_(version_ids)).limit(limit).all() if version_ids else []
        for row in component_links:
            relationships.append({"source_entity_type": "ProductVersion", "source_entity_id": str(row.product_version_id), "relationship_type": "PRODUCT_VERSION_USES_COMPONENT", "target_entity_type": "Component", "target_entity_id": str(row.component_id), "provenance": "product_components"})
        supplier_links = db.query(ComponentSupplier).filter(ComponentSupplier.tenant_id == tenant, ComponentSupplier.component_id.in_(component_ids)).limit(limit).all() if component_ids else []
        for row in supplier_links:
            relationships.append({"source_entity_type": "Component", "source_entity_id": str(row.component_id), "relationship_type": "COMPONENT_SUPPLIED_BY_SUPPLIER", "target_entity_type": "Supplier", "target_entity_id": str(row.supplier_id), "provenance": "component_suppliers"})

        collections = {
            "products": [_safe(row, ("product_identifier", "name", "lifecycle_status")) for row in products],
            "product_versions": [_safe(row, ("version_identifier", "product_id", "lifecycle_status", "release_timestamp")) for row in versions],
            "complaints": [_safe(row, ("complaint_identifier", "product_id", "product_version_id", "lot_batch_id", "status", "event_timestamp")) for row in complaints],
            "investigations": [_safe(row, ("investigation_identifier", "product_id", "status")) for row in investigations],
            "changes": [_safe(row, ("change_identifier", "change_type", "status", "event_timestamp")) for row in changes],
            "components": [_safe(row, ("component_identifier", "name", "revision", "status")) for row in components],
            "suppliers": [_safe(row, ("supplier_identifier", "name", "status")) for row in suppliers],
            "sites": [_safe(row, ("site_identifier", "name", "status")) for row in sites],
            "lots": [_safe(row, ("lot_identifier", "product_version_id", "manufacturing_site_id", "status")) for row in lots],
            "requirements": [_safe(row, ("requirement_identifier", "product_version_id", "status")) for row in requirements],
            "risks": [_safe(row, ("risk_identifier", "product_version_id", "status")) for row in risks],
            "failure_modes": [_safe(row, ("failure_mode_identifier", "name")) for row in failure_modes],
            "controls": [_safe(row, ("control_identifier", "control_type", "status")) for row in controls],
            "evidence": [_safe(row, ("evidence_identifier", "investigation_id", "evidence_type", "title", "reliability_status", "source_reference")) for row in evidence],
        }
        ai_safe_context = []
        allowed_fields = {"id", "product_identifier", "version_identifier", "complaint_identifier", "investigation_identifier", "evidence_identifier", "component_identifier", "supplier_identifier", "site_identifier", "lot_identifier", "requirement_identifier", "risk_identifier", "failure_mode_identifier", "control_identifier", "name", "title", "product_id", "product_version_id", "investigation_id", "status", "lifecycle_status", "reliability_status", "evidence_type", "source_reference"}
        for entity_type, records in collections.items():
            for record in records:
                built, decision = build_context(record, authorized_fields=allowed_fields, tenant_id=str(tenant), record_tenant_id=str(tenant))
                if decision.allowed:
                    ai_safe_context.append({"entity_type": entity_type, "record": built})

        return {
            "root_entity": {"tenant_id": str(tenant), "product_id": str(request.product_id) if request.product_id else None, "product_version_id": str(request.product_version_id) if request.product_version_id else None},
            **collections,
            "relationships": relationships[:limit],
            "ai_safe_context": ai_safe_context[:limit],
            "limitations": ["RELATIONSHIPS_ARE_NOT_CAUSAL", "UNREPRESENTED_RELATIONSHIPS_OMITTED"],
            "retrieval_metadata": {"tenant_scoped": True, "bounded_limit": limit, "authorized_only": True},
        }
