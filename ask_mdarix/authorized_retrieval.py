"""Small, server-authorized Day 27 retrieval surface.

This service deliberately resolves only Product, ProductVersion, and Evidence.
Every query is tenant-scoped and ProductVersion resolution verifies the
Product relationship before returning a record.
"""
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from backend.app.ai_boundary import build_context
from backend.app.db.models.foundation import Evidence, Product, ProductVersion


@dataclass(frozen=True)
class AuthorizedRetrievalRequest:
    tenant_id: UUID
    product_id: UUID | None = None
    product_identifier: str | None = None
    product_version_id: UUID | None = None
    product_version_identifier: str | None = None
    evidence_id: UUID | None = None
    evidence_identifier: str | None = None
    product_scope_id: UUID | None = None
    limit: int = 25


@dataclass(frozen=True)
class AuthorizedRetrievalResult:
    products: tuple[dict[str, Any], ...]
    product_versions: tuple[dict[str, Any], ...]
    evidence: tuple[dict[str, Any], ...]
    ai_context: tuple[dict[str, Any], ...]
    limitations: tuple[str, ...]


def _safe_product(row: Product) -> dict[str, Any]:
    return {"id": str(row.id), "identifier": row.product_identifier, "title": row.name,
            "description": row.description, "status": row.lifecycle_status,
            "provenance": {"source_system": row.source_system, "source_identifier": row.source_identifier,
                           "source_timestamp": row.source_timestamp.isoformat() if row.source_timestamp else None}}


def _safe_version(row: ProductVersion) -> dict[str, Any]:
    return {"id": str(row.id), "identifier": row.version_identifier, "title": row.version_identifier,
            "description": row.description, "status": row.lifecycle_status, "product_id": str(row.product_id),
            "effective_time": row.release_timestamp.isoformat() if row.release_timestamp else None,
            "provenance": {"source_system": row.source_system, "source_identifier": row.source_identifier}}


def _safe_evidence(row: Evidence) -> dict[str, Any]:
    return {"id": str(row.id), "identifier": row.evidence_identifier, "title": row.title,
            "description": row.content, "status": row.reliability_status, "type": row.evidence_type,
            "investigation_id": str(row.investigation_id) if row.investigation_id else None,
            "source_reference": row.source_reference,
            "provenance": {"source_system": row.source_system, "source_identifier": row.source_identifier,
                           "source_timestamp": row.source_timestamp.isoformat() if row.source_timestamp else None,
                           "ingestion_time": row.ingestion_timestamp.isoformat() if row.ingestion_timestamp else None}}


class AuthorizedRetrievalService:
    AI_FIELDS = {"id", "identifier", "title", "description", "status", "type", "product_id", "investigation_id", "effective_time", "source_reference", "provenance"}

    def retrieve(self, db: Session, request: AuthorizedRetrievalRequest) -> AuthorizedRetrievalResult:
        limit = max(1, min(request.limit, 100))
        products: list[Product] = []
        versions: list[ProductVersion] = []
        evidence: list[Evidence] = []

        if request.product_id or request.product_identifier:
            query = db.query(Product).filter(Product.tenant_id == request.tenant_id)
            if request.product_id:
                query = query.filter(Product.id == request.product_id)
            if request.product_identifier:
                query = query.filter(Product.product_identifier == request.product_identifier)
            products = query.limit(limit).all()

        product_ids = {row.id for row in products}
        if request.product_scope_id:
            product_ids.add(request.product_scope_id)

        if request.product_version_id or request.product_version_identifier:
            query = db.query(ProductVersion).filter(ProductVersion.tenant_id == request.tenant_id)
            if request.product_version_id:
                query = query.filter(ProductVersion.id == request.product_version_id)
            if request.product_version_identifier:
                query = query.filter(ProductVersion.version_identifier == request.product_version_identifier)
            if product_ids:
                query = query.filter(ProductVersion.product_id.in_(product_ids))
            versions = query.limit(limit).all()

        if request.evidence_id or request.evidence_identifier:
            query = db.query(Evidence).filter(Evidence.tenant_id == request.tenant_id)
            if request.evidence_id:
                query = query.filter(Evidence.id == request.evidence_id)
            if request.evidence_identifier:
                query = query.filter(Evidence.evidence_identifier == request.evidence_identifier)
            evidence = query.limit(limit).all()

        safe_records = [_safe_product(row) for row in products] + [_safe_version(row) for row in versions] + [_safe_evidence(row) for row in evidence]
        context: list[dict[str, Any]] = []
        for record in safe_records:
            built, decision = build_context(record, authorized_fields=self.AI_FIELDS, tenant_id=str(request.tenant_id), record_tenant_id=str(request.tenant_id))
            if decision.allowed:
                context.append(built)
        return AuthorizedRetrievalResult(tuple(_safe_product(row) for row in products), tuple(_safe_version(row) for row in versions), tuple(_safe_evidence(row) for row in evidence), tuple(context), ())
