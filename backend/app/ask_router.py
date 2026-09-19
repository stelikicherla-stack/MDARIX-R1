"""Authenticated, non-chat Ask MDARIX control-plane endpoint."""
from uuid import UUID, uuid4
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ask_mdarix import QueryInterpreter
from ask_mdarix.retrieval import build_retrieval_plan
from auth.service import auth_service
from backend.app.db.models.foundation import (
    Evidence, FeatureEntitlement, Hypothesis, HypothesisEvidence, PlanDefinition,
    Investigation, Product, ProductVersion, Tenant, TenantPlanAssignment, Unknown,
)
from backend.app.db.models.ask import InvestigationSessionRecord
from backend.app.db.session import get_db
from backend.app.enterprise_audit import make_audit_event
from ask_mdarix.authorized_retrieval import AuthorizedRetrievalRequest, AuthorizedRetrievalService
from ask_mdarix.lifecycle_retrieval import LifecycleRetrievalRequest, LifecycleRetrievalService

router = APIRouter(prefix="/api/v1/ask", tags=["Ask MDARIX"])
ASK_FEATURE = "ASK_MDARIX"
DAY27_FAULT_FLAG = "DAY27_LIVE_DEPENDENCY_FAILURE"
DAY30_FAULT_FLAG = "DAY30_LIVE_DEPENDENCY_FAILURE"
DAY34_FAULT_FLAG = "DAY34_LIVE_DEPENDENCY_FAILURE"
_EXTERNAL_WRITE_TERMS = ("trackwise", "sap", "plm", "qms", "capa")
_EXTERNAL_WRITE_ACTIONS = ("close", "create", "update", "modify", "delete", "send", "change")


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    # Accepted only as display/request context; never used as authority.
    tenant_id: str | None = None
    role: str | None = None
    entitlement: str | None = None
    session_id: str | None = None
    product_id: str | None = None
    product_identifier: str | None = None
    product_version_id: str | None = None
    product_version_identifier: str | None = None
    evidence_id: str | None = None
    evidence_identifier: str | None = None
    complaint_id: str | None = None
    investigation_id: str | None = None


def _authenticated_context(request: Request) -> dict:
    token = request.cookies.get("mdarix_session", "")
    try:
        return auth_service.context(token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail={"code": "UNAUTHENTICATED", "message": "Authentication required"}) from exc


def _has_ask_entitlement(db: Session, tenant_id: str) -> bool:
    """Evaluate the existing server-side plan/feature tables on every call."""
    row = (
        db.query(TenantPlanAssignment)
        .join(PlanDefinition, PlanDefinition.id == TenantPlanAssignment.plan_id)
        .join(FeatureEntitlement, FeatureEntitlement.plan_id == PlanDefinition.id)
        .filter(
            TenantPlanAssignment.tenant_id == tenant_id,
            TenantPlanAssignment.status == "ACTIVE",
            PlanDefinition.status == "ACTIVE",
            FeatureEntitlement.feature_code == ASK_FEATURE,
            FeatureEntitlement.enabled.is_(True),
            FeatureEntitlement.status == "ACTIVE",
        )
        .first()
    )
    return row is not None


def _record_audit(db: Session, *, tenant_id: UUID | str, actor: str, action: str, correlation_id: str, details: dict | None = None) -> None:
    """Record only safe Ask lifecycle metadata through the existing audit model."""
    db.add(make_audit_event(
        tenant_id=tenant_id,
        actor_ref=actor,
        action=action,
        entity_type="Ask",
        correlation_id=correlation_id,
        details=details or {},
    ))


def _temporal_audit_details(spec) -> dict:
    details = {"temporal_mode": spec.temporal_mode.value}
    if spec.event_start:
        details["event_start"] = spec.event_start.isoformat()
    if spec.event_end:
        details["event_end"] = spec.event_end.isoformat()
    if spec.knowledge_time:
        details["temporal_cutoff"] = spec.knowledge_time.isoformat()
    return details


def _is_external_write_request(question: str) -> bool:
    normalized = question.casefold()
    return any(term in normalized for term in _EXTERNAL_WRITE_TERMS) and any(action in normalized for action in _EXTERNAL_WRITE_ACTIONS)


def _validate_product_version_scope(db: Session, *, tenant_id: UUID, product_version_id: UUID | None, product_id: UUID | None, investigation_id: UUID | None) -> None:
    if product_version_id is None:
        return
    version = db.query(ProductVersion).filter(
        ProductVersion.tenant_id == tenant_id,
        ProductVersion.id == product_version_id,
    ).first()
    if version is None:
        raise HTTPException(status_code=404, detail={"code": "PRODUCT_VERSION_NOT_FOUND", "message": "ProductVersion is not available for this tenant"})
    effective_product_id = product_id
    if effective_product_id is None and investigation_id is not None:
        investigation = db.query(Investigation).filter(
            Investigation.tenant_id == tenant_id,
            Investigation.id == investigation_id,
        ).first()
        if investigation is not None:
            effective_product_id = investigation.product_id
    if effective_product_id is not None and version.product_id != effective_product_id:
        raise HTTPException(status_code=422, detail={"code": "PRODUCT_VERSION_SCOPE_MISMATCH", "message": "ProductVersion is not compatible with the requested Product scope"})


def _structured_intelligence(*, retrieval, lifecycle, intelligence, spec) -> dict:
    """Compose the existing bounded engines into the Ask investigation contract.

    This is deliberately a presentation/composition boundary. It does not
    create a second hypothesis, Challenger, Failure Chain, Scenario, or Brief
    engine and it never upgrades correlation, unknowns, or derived analysis
    into a source fact or human decision.
    """
    evidence = list(retrieval.evidence)
    limitations = list(retrieval.limitations)
    if lifecycle:
        limitations.extend(lifecycle.get("limitations", []))
    return {
        "finding": None,
        "supporting_evidence": [item for item in evidence if item.get("fact_type") == "supporting"],
        "contradicting_evidence": [item for item in evidence if item.get("fact_type") == "contradicting"],
        "unknowns": (intelligence or {}).get("unknowns", []),
        "missing_evidence": [],
        "hypotheses": (intelligence or {}).get("hypotheses", []),
        "alternative_hypotheses": [],
        "failure_chain_assessment": None,
        "scenario_findings": [],
        "decision_brief": None,
        "sources_provenance": [item.get("provenance", {}) for item in evidence],
        "temporal_scope": _temporal_audit_details(spec),
        "product_scope": lifecycle.get("root_entity", {}).get("product_id") if lifecycle else None,
        "product_version_scope": lifecycle.get("root_entity", {}).get("product_version_id") if lifecycle else None,
        "limitations": sorted(set(limitations)),
        "human_review_required": bool(evidence or intelligence),
        "causality_state": "NOT_ESTABLISHED",
        "status": "INSUFFICIENT_EVIDENCE" if not evidence and not intelligence else "READY_FOR_REVIEW",
    }


@router.post("/")
def ask(request: Request, data: AskRequest, db: Session = Depends(get_db)) -> dict:
    context = _authenticated_context(request)
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid4())
    tenant = db.query(Tenant).filter(Tenant.id == context["tenant_id"]).first()
    if tenant is None or str(tenant.status).lower() not in {"active", "enabled"}:
        if tenant is not None:
            _record_audit(db, tenant_id=context["tenant_id"], actor=context["user_id"], action="ASK_AUTHORIZATION_DENIED", correlation_id=correlation_id, details={"reason": "TENANT_UNAVAILABLE"})
            db.commit()
        raise HTTPException(status_code=403, detail={"code": "TENANT_UNAVAILABLE", "message": "Tenant is not available"})
    if not _has_ask_entitlement(db, context["tenant_id"]):
        _record_audit(db, tenant_id=context["tenant_id"], actor=context["user_id"], action="ASK_AUTHORIZATION_DENIED", correlation_id=correlation_id, details={"reason": "ASK_NOT_ENTITLED"})
        db.commit()
        raise HTTPException(status_code=403, detail={"code": "ASK_NOT_ENTITLED", "message": "Ask MDARIX is not enabled for this tenant"})

    if _is_external_write_request(data.question):
        _record_audit(db, tenant_id=context["tenant_id"], actor=context["user_id"], action="ASK_AUTHORIZATION_DENIED", correlation_id=correlation_id, details={"reason": "EXTERNAL_WRITE_DISABLED"})
        db.commit()
        raise HTTPException(status_code=403, detail={"code": "EXTERNAL_WRITE_DISABLED", "message": "External system write-back is disabled in R1"})

    _record_audit(db, tenant_id=context["tenant_id"], actor=context["user_id"], action="ASK_QUERY_RECEIVED", correlation_id=correlation_id)
    _validate_product_version_scope(
        db,
        tenant_id=UUID(context["tenant_id"]),
        product_version_id=_uuid_or_none(data.product_version_id),
        product_id=_uuid_or_none(data.product_id),
        investigation_id=_uuid_or_none(data.investigation_id),
    )
    if data.session_id:
        try:
            session = db.query(InvestigationSessionRecord).filter(
                InvestigationSessionRecord.id == UUID(data.session_id),
                InvestigationSessionRecord.tenant_id == UUID(context["tenant_id"]),
                InvestigationSessionRecord.owner_user_id == context["user_id"],
                InvestigationSessionRecord.status == "ACTIVE",
            ).first()
        except (ValueError, TypeError):
            session = None
        if session is None:
            _record_audit(db, tenant_id=context["tenant_id"], actor=context["user_id"], action="ASK_AUTHORIZATION_DENIED", correlation_id=correlation_id, details={"reason": "ASK_SESSION_NOT_FOUND"})
            db.commit()
            raise HTTPException(status_code=404, detail={"code": "ASK_SESSION_NOT_FOUND", "message": "Investigation session is not available"})
    else:
        session = InvestigationSessionRecord(
            tenant_id=UUID(context["tenant_id"]), owner_user_id=context["user_id"],
            correlation_id=correlation_id, created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
        )
        db.add(session)
        db.flush()

    if data.investigation_id:
        investigation_id = _uuid_or_none(data.investigation_id)
        investigation = db.query(Investigation).filter(
            Investigation.id == investigation_id,
            Investigation.tenant_id == UUID(context["tenant_id"]),
        ).first() if investigation_id else None
        if investigation is None:
            _record_audit(db, tenant_id=context["tenant_id"], actor=context["user_id"], action="ASK_AUTHORIZATION_DENIED", correlation_id=correlation_id, details={"reason": "INVESTIGATION_NOT_FOUND"})
            db.commit()
            raise HTTPException(status_code=404, detail={"code": "INVESTIGATION_NOT_FOUND", "message": "Investigation is not available for this tenant"})

    # The server-side session context is authoritative. Client tenant, owner,
    # role, entitlement, and session fields are deliberately ignored as authority.
    spec = QueryInterpreter().interpret(data.question)
    plan = build_retrieval_plan(spec)
    retrieval_requested = any((data.product_id, data.product_identifier, data.product_version_id, data.product_version_identifier, data.evidence_id, data.evidence_identifier))
    lifecycle_requested = any((data.product_id, data.product_version_id, data.complaint_id, data.investigation_id, data.evidence_id))
    try:
        # Test/development-only live validation seam. It is server-configured,
        # disabled by default, never client-triggered, and fail-closed in
        # production mode. It runs only after all authorization and session
        # ownership checks have succeeded.
        if (
            (os.environ.get(DAY27_FAULT_FLAG) == "1" or os.environ.get(DAY30_FAULT_FLAG) == "1" or os.environ.get(DAY34_FAULT_FLAG) == "1")
            and os.environ.get("MDARIX_ENV", "development").lower() != "production"
            and (retrieval_requested or lifecycle_requested)
        ):
            raise RuntimeError("controlled Day 27 retrieval dependency failure")
        retrieval = AuthorizedRetrievalService().retrieve(db, AuthorizedRetrievalRequest(
            tenant_id=UUID(context["tenant_id"]),
            product_id=_uuid_or_none(data.product_id), product_identifier=data.product_identifier,
            product_version_id=_uuid_or_none(data.product_version_id), product_version_identifier=data.product_version_identifier,
            evidence_id=_uuid_or_none(data.evidence_id), evidence_identifier=data.evidence_identifier,
            limit=plan.limit or 25,
        ))
        lifecycle = LifecycleRetrievalService().retrieve(db, LifecycleRetrievalRequest(
            tenant_id=UUID(context["tenant_id"]),
            product_id=_uuid_or_none(data.product_id),
            product_version_id=_uuid_or_none(data.product_version_id),
            complaint_id=_uuid_or_none(data.complaint_id),
            investigation_id=_uuid_or_none(data.investigation_id),
            evidence_id=_uuid_or_none(data.evidence_id),
            limit=plan.limit or 25,
        )) if lifecycle_requested else None
    except Exception as exc:
        _record_audit(db, tenant_id=context["tenant_id"], actor=context["user_id"], action="ASK_RETRIEVAL_FAILED", correlation_id=correlation_id, details={"reason": "RETRIEVAL_UNAVAILABLE"})
        db.commit()
        raise HTTPException(status_code=503, detail={"code": "RETRIEVAL_UNAVAILABLE", "message": "Authorized retrieval is temporarily unavailable", "correlation_id": correlation_id}) from exc
    if retrieval_requested or lifecycle_requested:
        _record_audit(db, tenant_id=context["tenant_id"], actor=context["user_id"], action="ASK_RETRIEVAL_EXECUTED", correlation_id=correlation_id, details={"result_count": len(retrieval.ai_context)})
    _record_audit(db, tenant_id=context["tenant_id"], actor=context["user_id"], action="ASK_QUERY_PROCESSED", correlation_id=correlation_id, details={"status": "INTERPRETED", **_temporal_audit_details(spec)})
    session.updated_at = datetime.now(timezone.utc)
    db.commit()
    intelligence = None
    if data.investigation_id:
        investigation_id = _uuid_or_none(data.investigation_id)
        if investigation_id is not None:
            hypotheses = db.query(Hypothesis).filter(
                Hypothesis.tenant_id == UUID(context["tenant_id"]),
                Hypothesis.investigation_id == investigation_id,
            ).all()
            hypothesis_ids = [item.id for item in hypotheses]
            unknowns = db.query(Unknown).filter(
                Unknown.tenant_id == UUID(context["tenant_id"]),
                Unknown.investigation_id == investigation_id,
            ).all()
            links = db.query(HypothesisEvidence).filter(
                HypothesisEvidence.tenant_id == UUID(context["tenant_id"]),
                HypothesisEvidence.hypothesis_id.in_(hypothesis_ids) if hypothesis_ids else False,
            ).all()
            evidence_ids = [link.evidence_id for link in links]
            evidence_rows = db.query(Evidence).filter(
                Evidence.tenant_id == UUID(context["tenant_id"]),
                Evidence.id.in_(evidence_ids) if evidence_ids else False,
            ).all()
            evidence_by_id = {row.id: row for row in evidence_rows}
            intelligence = {
                "hypotheses": [{"id": str(row.id), "statement": row.statement, "status": row.status, "origin": row.origin} for row in hypotheses],
                "unknowns": [{"id": str(row.id), "category": row.category, "description": row.description, "status": row.status} for row in unknowns],
                "provenance": [{"hypothesis_id": str(link.hypothesis_id), "evidence_id": str(link.evidence_id), "evidence_identifier": evidence_by_id[link.evidence_id].evidence_identifier, "relation_type": link.relation_type, "created_by_type": link.created_by_type} for link in links if link.evidence_id in evidence_by_id],
                "counts": {"hypotheses": len(hypotheses), "unknowns": len(unknowns), "provenance": len(links)},
            }
    return {
        "status": "INTERPRETED",
        "correlation_id": correlation_id,
        "session_id": str(session.id),
        "user_id": context["user_id"],
        "tenant_id": context["tenant_id"],
        "active_role": context["active_role"],
        "specification": spec.model_dump(mode="json"),
        "retrieval_plan": plan.__dict__,
        "execution": "AUTHORIZED_LIFECYCLE_RETRIEVAL" if lifecycle_requested else ("AUTHORIZED_RETRIEVAL_FOUNDATION" if retrieval_requested else "CONTROLLED_FOUNDATION_ONLY"),
        "retrieval": {"products": retrieval.products, "product_versions": retrieval.product_versions, "evidence": retrieval.evidence, "count": len(retrieval.ai_context)},
        "ai_safe_context": retrieval.ai_context,
        "lifecycle": lifecycle,
        "intelligence": intelligence,
        "structured_intelligence": _structured_intelligence(
            retrieval=retrieval, lifecycle=lifecycle, intelligence=intelligence, spec=spec,
        ),
        "message": "Question interpreted and bounded authorized lifecycle retrieval completed. Relationships are not causal and no human decision conclusion is generated." if (retrieval_requested or lifecycle_requested) else "Question interpreted. Add an authorized lifecycle scope to execute bounded retrieval.",
    }


def _uuid_or_none(value: str | None) -> UUID | None:
    if not value:
        return None
    try:
        return UUID(value)
    except (ValueError, TypeError):
        return None
