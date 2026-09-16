import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import or_, text
from sqlalchemy.orm import Session

from backend.app.db.models.evidence_intelligence import EvidenceChunk, EvidenceEntityLink, EvidenceObservation
from backend.app.db.models.foundation import Evidence, Investigation
from backend.app.product360.service import Product360Service, rowdict
from graph.service import GraphError, RealityGraphService
from investigation_workspace.schemas import InvestigationWorkspaceRequest, InvestigationWorkspaceResponse
from retrieval.schemas import RetrievalRequest, RetrievalResponse
from retrieval.service import RetrievalError, TrustedRetrievalService


WORKSPACE_VERSION = "R1-Day10"


class InvestigationWorkspaceError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class InvestigationWorkspaceService:
    def __init__(
        self,
        product_service: Product360Service | None = None,
        graph_service: RealityGraphService | None = None,
        retrieval_service: TrustedRetrievalService | None = None,
    ) -> None:
        self.product_service = product_service or Product360Service()
        self.graph_service = graph_service or RealityGraphService()
        self.retrieval_service = retrieval_service or TrustedRetrievalService()

    def workspace(self, db: Session, request: InvestigationWorkspaceRequest) -> InvestigationWorkspaceResponse:
        if request.tenant_id is None:
            raise InvestigationWorkspaceError("TENANT_REQUIRED", "tenant_id is required")

        investigation = (
            db.query(Investigation)
            .filter(Investigation.tenant_id == request.tenant_id, Investigation.id == request.investigation_id)
            .first()
        )
        if investigation is None:
            raise InvestigationWorkspaceError("INVESTIGATION_NOT_FOUND", "Investigation not found")

        product_version_id = self._select_product_version_id(db, request.tenant_id, investigation.id)
        product_context = self._product_context(investigation, product_version_id, request)
        relationship_context = self._relationship_context(investigation.id)
        evidence_context = self._evidence_context(db, request.tenant_id, investigation, request.temporal_mode, request.as_of)
        retrieval_context = self._retrieval_context(db, request, investigation, product_version_id) if request.include_retrieval else None
        temporal_context = self._temporal_context(product_context, request)
        limitations = self._limitations(product_context, evidence_context, retrieval_context)

        return InvestigationWorkspaceResponse(
            investigation=self._investigation_header(investigation),
            product_context=product_context,
            temporal_context=temporal_context,
            relationship_context=relationship_context,
            evidence_context=evidence_context,
            retrieval_context=retrieval_context,
            limitations=limitations,
            guardrails={
                "human_authority_required": True,
                "generates_causality": False,
                "retrieval_rank_semantics": "retrieval relevance only; not truth, confidence, causality, regulatory significance, or probability",
                "ground_truth_isolation": "evaluation ground truth is not used by the investigation workspace",
            },
            metadata={
                "tenant_id": str(request.tenant_id),
                "workspace_version": WORKSPACE_VERSION,
                "generated_at": utcnow().isoformat(),
                "ground_truth_used": False,
            },
        )

    def _product_context(self, investigation: Investigation, product_version_id: str | None, request: InvestigationWorkspaceRequest) -> dict[str, Any]:
        view = self.product_service.product360(
            str(investigation.product_id),
            version_id=product_version_id,
            as_of=request.as_of,
            mode=request.temporal_mode,
        )
        return {
            "product": view.product,
            "selected_version": view.selected_version,
            "overview": view.overview,
            "configuration": view.configuration,
            "changes": view.changes,
            "manufacturing": view.manufacturing,
            "complaints": view.complaints,
            "risks": view.risks,
            "controls": view.controls,
            "limitations": view.limitations,
            "provenance": view.provenance,
        }

    def _investigation_header(self, investigation: Investigation) -> dict[str, Any]:
        return {
            "id": str(investigation.id),
            "investigation_identifier": investigation.investigation_identifier,
            "product_id": str(investigation.product_id),
            "investigation_question": investigation.investigation_question,
            "status": investigation.status,
            "opened_at": investigation.opened_at.isoformat() if investigation.opened_at else None,
            "closed_at": investigation.closed_at.isoformat() if investigation.closed_at else None,
            "owner_ref": investigation.owner_ref,
        }

    def _relationship_context(self, investigation_id: uuid.UUID) -> dict[str, Any]:
        try:
            graph = self.graph_service.get_investigation_graph(str(investigation_id), depth=2)
            return graph.model_dump(mode="json")
        except GraphError as exc:
            return {
                "nodes": [],
                "relationships": [],
                "metadata": {
                    "warning": exc.message,
                    "relationship_semantics": "graph connectivity only; not causality",
                },
            }

    def _evidence_context(
        self,
        db: Session,
        tenant_id: uuid.UUID,
        investigation: Investigation,
        temporal_mode: str,
        as_of: datetime | None,
    ) -> list[dict[str, Any]]:
        rows = self._investigation_evidence_query(db, tenant_id, investigation.id, temporal_mode, as_of).all()
        return [self._evidence_item(db, tenant_id, investigation, evidence) for evidence in rows]

    def _investigation_evidence_query(self, db: Session, tenant_id: uuid.UUID, investigation_id: uuid.UUID, temporal_mode: str, as_of: datetime | None):
        source_identifier = db.query(Investigation.source_identifier).filter(Investigation.tenant_id == tenant_id, Investigation.id == investigation_id).scalar()
        q = db.query(Evidence).filter(Evidence.tenant_id == tenant_id)
        q = q.filter(
            or_(
                Evidence.investigation_id == investigation_id,
                Evidence.id.in_(
                text(
                    "SELECT evidence_id FROM investigation_evidence "
                    "WHERE tenant_id=:tenant_id AND investigation_id=:investigation_id"
                )
                .bindparams(tenant_id=tenant_id, investigation_id=investigation_id)
                .columns(evidence_id=Evidence.id.type)
                ),
                Evidence.evidence_identifier.in_(
                    text(
                        "SELECT raw_payload->>'evidence_id' FROM staged_source_records "
                        "WHERE tenant_id=:tenant_id AND record_type='evidence_metadata' "
                        "AND raw_payload->>'investigation_id'=:source_identifier"
                    )
                    .bindparams(tenant_id=tenant_id, source_identifier=source_identifier or "")
                    .columns(evidence_identifier=Evidence.evidence_identifier.type)
                ),
            )
        )
        if as_of and temporal_mode == "known":
            q = q.filter(Evidence.ingestion_timestamp.is_not(None), Evidence.ingestion_timestamp <= as_of)
        if as_of and temporal_mode == "event":
            q = q.filter((Evidence.effective_timestamp.is_(None)) | (Evidence.effective_timestamp <= as_of))
        return q.order_by(Evidence.source_timestamp.nulls_last(), Evidence.evidence_identifier)

    def _evidence_item(self, db: Session, tenant_id: uuid.UUID, investigation: Investigation, evidence: Evidence) -> dict[str, Any]:
        chunks = (
            db.query(EvidenceChunk)
            .filter(EvidenceChunk.tenant_id == tenant_id, EvidenceChunk.evidence_id == evidence.id)
            .order_by(EvidenceChunk.sequence_number)
            .all()
        )
        observations = (
            db.query(EvidenceObservation)
            .filter(EvidenceObservation.tenant_id == tenant_id, EvidenceObservation.evidence_id == evidence.id)
            .order_by(EvidenceObservation.created_at)
            .all()
        )
        links = (
            db.query(EvidenceEntityLink)
            .filter(EvidenceEntityLink.tenant_id == tenant_id, EvidenceEntityLink.evidence_id == evidence.id)
            .all()
        )
        link_payload = [
            {
                "entity_type": link.entity_type,
                "entity_id": str(link.entity_id) if link.entity_id else None,
                "raw_reference": link.raw_reference,
                "resolution_status": link.resolution_status,
                "source": "evidence_entity_links",
            }
            for link in links
        ]
        if not link_payload:
            link_payload = [
                {
                    "entity_type": "Investigation",
                    "entity_id": str(investigation.id),
                    "raw_reference": investigation.investigation_identifier,
                    "resolution_status": "RESOLVED",
                    "source": "workspace_investigation_context",
                },
                {
                    "entity_type": "Product",
                    "entity_id": str(investigation.product_id),
                    "raw_reference": str(investigation.product_id),
                    "resolution_status": "RESOLVED",
                    "source": "workspace_investigation_context",
                },
            ]
        chunk_payload = [
            {
                "chunk_id": str(chunk.id),
                "sequence_number": chunk.sequence_number,
                "source_anchor": chunk.source_anchor or {},
                "excerpt": (chunk.source_anchor or {}).get("excerpt") or chunk.text_content[:240],
                "materialized": True,
            }
            for chunk in chunks
        ]
        if not chunk_payload and evidence.content:
            chunk_payload = [
                {
                    "chunk_id": None,
                    "sequence_number": 1,
                    "source_anchor": {
                        "source": evidence.source_reference or evidence.document_ref or evidence.evidence_identifier,
                        "locator": "evidence.content",
                        "fallback": "workspace_content_excerpt",
                    },
                    "excerpt": evidence.content[:240],
                    "materialized": False,
                }
            ]
        return {
            "id": str(evidence.id),
            "evidence_identifier": evidence.evidence_identifier,
            "evidence_type": evidence.evidence_type,
            "title": evidence.title,
            "source_reference": evidence.source_reference,
            "reliability_status": evidence.reliability_status,
            "fact_type": evidence.fact_type,
            "temporal": {
                "effective_timestamp": evidence.effective_timestamp.isoformat() if evidence.effective_timestamp else None,
                "recorded_timestamp": evidence.recorded_timestamp.isoformat() if evidence.recorded_timestamp else None,
                "ingestion_timestamp": evidence.ingestion_timestamp.isoformat() if evidence.ingestion_timestamp else None,
            },
            "chunks": chunk_payload,
            "observations": [
                {
                    "observation_id": str(obs.id),
                    "statement": obs.statement,
                    "observation_type": obs.observation_type,
                    "extraction_method": obs.extraction_method,
                    "source_anchor": obs.source_anchor or {},
                    "quality_status": obs.quality_status,
                    "limitations": obs.limitations or [],
                }
                for obs in observations
            ],
            "entity_links": link_payload,
        }

    def _retrieval_context(
        self,
        db: Session,
        request: InvestigationWorkspaceRequest,
        investigation: Investigation,
        product_version_id: str | None,
    ) -> RetrievalResponse:
        retrieval_request = RetrievalRequest(
            tenant_id=request.tenant_id,
            investigation_id=request.investigation_id,
            product_id=investigation.product_id,
            product_version_id=uuid.UUID(product_version_id) if product_version_id else None,
            query_text=investigation.investigation_question,
            retrieval_mode="hybrid",
            temporal_mode=request.temporal_mode,
            event_as_of=request.as_of if request.temporal_mode == "event" else None,
            knowledge_as_of=request.as_of if request.temporal_mode == "known" else None,
            top_k=request.retrieval_top_k,
        )
        try:
            return self.retrieval_service.retrieve(db, retrieval_request)
        except RetrievalError as exc:
            raise InvestigationWorkspaceError("RETRIEVAL_FAILED", str(exc)) from exc

    def _temporal_context(self, product_context: dict[str, Any], request: InvestigationWorkspaceRequest) -> dict[str, Any]:
        return {
            "mode": request.temporal_mode,
            "as_of": request.as_of.isoformat() if request.as_of else None,
            "event_time_distinct_from_known_time": True,
            "late_arriving_evidence_count": sum(
                1
                for item in product_context.get("limitations", [])
                if item.get("code") == "LATE_ARRIVING_EVIDENCE"
            ),
        }

    def _limitations(
        self,
        product_context: dict[str, Any],
        evidence_context: list[dict[str, Any]],
        retrieval_context: RetrievalResponse | None,
    ) -> list[dict[str, Any]]:
        limitations = list(product_context.get("limitations", []))
        if not evidence_context:
            limitations.append({"code": "NO_DIRECT_EVIDENCE", "severity": "WARNING", "description": "No direct evidence records are attached to this investigation."})
        fallback_chunks = sum(
            1
            for evidence in evidence_context
            for chunk in evidence["chunks"]
            if not chunk["materialized"]
        )
        if fallback_chunks:
            limitations.append({"code": "MISSING_MATERIALIZED_CHUNKS", "severity": "INFO", "description": f"{fallback_chunks} evidence records are shown with workspace fallback source anchors."})
        unresolved = sum(
            1
            for evidence in evidence_context
            for link in evidence["entity_links"]
            if link["resolution_status"] != "RESOLVED"
        )
        if unresolved:
            limitations.append({"code": "UNRESOLVED_EVIDENCE_LINKS", "severity": "WARNING", "description": f"{unresolved} evidence entity links are unresolved."})
        if retrieval_context and retrieval_context.status != "COMPLETED":
            limitations.append({"code": retrieval_context.status, "severity": "WARNING", "description": "Trusted retrieval did not return complete contextual evidence."})
        limitations.append({"code": "NO_INVESTIGATION_CONCLUSION", "severity": "INFO", "description": "Workspace presents context only; regulated conclusions remain human decisions."})
        return limitations

    def _select_product_version_id(self, db: Session, tenant_id: uuid.UUID, investigation_id: uuid.UUID) -> str | None:
        value = db.execute(
            text(
                "SELECT c.product_version_id FROM investigation_complaints ic "
                "JOIN complaints c ON c.tenant_id=ic.tenant_id AND c.id=ic.complaint_id "
                "WHERE ic.tenant_id=:tenant_id AND ic.investigation_id=:investigation_id AND c.product_version_id IS NOT NULL "
                "ORDER BY c.event_timestamp NULLS LAST LIMIT 1"
            ),
            {"tenant_id": tenant_id, "investigation_id": investigation_id},
        ).scalar_one_or_none()
        return str(value) if value else None
