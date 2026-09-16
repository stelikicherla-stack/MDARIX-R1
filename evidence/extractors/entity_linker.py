import logging
import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from ai.schemas import EntityLinkCandidateSchema
from backend.app.db.models.foundation import (
    Change,
    Complaint,
    Component,
    Control,
    FailureMode,
    Investigation,
    LotBatch,
    ManufacturingSite,
    Product,
    ProductVersion,
    Requirement,
    Risk,
    Supplier,
)
from backend.app.db.models.evidence_intelligence import EvidenceEntityLink

logger = logging.getLogger(__name__)


class EntityLinker:
    """Resolves extracted entity candidate references to Day 5 canonical objects."""

    def resolve_and_link_entities(
        self,
        db: Session,
        tenant_id: uuid.UUID,
        evidence_id: uuid.UUID,
        observation_id: Optional[uuid.UUID],
        candidates: List[EntityLinkCandidateSchema],
    ) -> List[EvidenceEntityLink]:
        """Resolves entity references against canonical tables. Creates EvidenceEntityLink rows."""
        links: List[EvidenceEntityLink] = []

        for candidate in candidates:
            resolved_id, status = self._lookup_canonical_entity(
                db=db,
                tenant_id=tenant_id,
                entity_type=candidate.entity_type,
                raw_ref=candidate.raw_reference,
                identifier=candidate.candidate_identifier,
            )

            link = EvidenceEntityLink(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                evidence_id=evidence_id,
                observation_id=observation_id,
                entity_type=candidate.entity_type,
                entity_id=resolved_id,
                raw_reference=candidate.raw_reference,
                resolution_status=status,
                confidence_score=str(candidate.confidence),
            )
            db.add(link)
            links.append(link)

        db.flush()
        return links

    def _lookup_canonical_entity(
        self,
        db: Session,
        tenant_id: uuid.UUID,
        entity_type: str,
        raw_ref: str,
        identifier: Optional[str],
    ) -> tuple[Optional[uuid.UUID], str]:
        """Looks up entity in database by identifier or raw reference."""
        search_key = (identifier or raw_ref).strip()

        if entity_type == "Product":
            prod = (
                db.query(Product)
                .filter(
                    Product.tenant_id == tenant_id,
                    (Product.product_identifier == search_key) | (Product.name.ilike(f"%{search_key}%")),
                )
                .first()
            )
            if prod:
                return prod.id, "RESOLVED"

        elif entity_type == "ProductVersion":
            pv = (
                db.query(ProductVersion)
                .filter(ProductVersion.tenant_id == tenant_id, ProductVersion.version_identifier == search_key)
                .first()
            )
            if pv:
                return pv.id, "RESOLVED"

        elif entity_type == "Component":
            # Match component_identifier or revision
            comp = (
                db.query(Component)
                .filter(
                    Component.tenant_id == tenant_id,
                    (Component.component_identifier == search_key)
                    | (Component.name.ilike(f"%{search_key}%"))
                    | (Component.revision == search_key),
                )
                .first()
            )
            if comp:
                return comp.id, "RESOLVED"

        elif entity_type == "Supplier":
            sup = (
                db.query(Supplier)
                .filter(
                    Supplier.tenant_id == tenant_id,
                    (Supplier.supplier_identifier == search_key) | (Supplier.name.ilike(f"%{search_key}%")),
                )
                .first()
            )
            if sup:
                return sup.id, "RESOLVED"

        elif entity_type == "LotBatch":
            lot = (
                db.query(LotBatch)
                .filter(LotBatch.tenant_id == tenant_id, LotBatch.lot_identifier == search_key)
                .first()
            )
            if lot:
                return lot.id, "RESOLVED"

        elif entity_type == "Complaint":
            cmpl = (
                db.query(Complaint)
                .filter(Complaint.tenant_id == tenant_id, Complaint.complaint_identifier == search_key)
                .first()
            )
            if cmpl:
                return cmpl.id, "RESOLVED"

        elif entity_type == "Investigation":
            inv = (
                db.query(Investigation)
                .filter(Investigation.tenant_id == tenant_id, Investigation.investigation_identifier == search_key)
                .first()
            )
            if inv:
                return inv.id, "RESOLVED"

        elif entity_type == "Risk":
            risk = (
                db.query(Risk)
                .filter(Risk.tenant_id == tenant_id, Risk.risk_identifier == search_key)
                .first()
            )
            if risk:
                return risk.id, "RESOLVED"

        elif entity_type == "Control":
            ctrl = (
                db.query(Control)
                .filter(Control.tenant_id == tenant_id, Control.control_identifier == search_key)
                .first()
            )
            if ctrl:
                return ctrl.id, "RESOLVED"

        # Unresolved reference - preserve raw reference without creating fake DB object
        return None, "UNRESOLVED"
