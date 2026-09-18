"""Authenticated, non-chat Ask MDARIX control-plane endpoint."""
from uuid import UUID, uuid4
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ask_mdarix import QueryInterpreter
from ask_mdarix.retrieval import build_retrieval_plan
from auth.service import auth_service
from backend.app.db.models.foundation import FeatureEntitlement, PlanDefinition, Tenant, TenantPlanAssignment
from backend.app.db.models.ask import InvestigationSessionRecord
from backend.app.db.session import get_db
from backend.app.enterprise_audit import make_audit_event

router = APIRouter(prefix="/api/v1/ask", tags=["Ask MDARIX"])
ASK_FEATURE = "ASK_MDARIX"


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    # Accepted only as display/request context; never used as authority.
    tenant_id: str | None = None
    role: str | None = None
    entitlement: str | None = None
    session_id: str | None = None


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

    _record_audit(db, tenant_id=context["tenant_id"], actor=context["user_id"], action="ASK_QUERY_RECEIVED", correlation_id=correlation_id)
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

    # The server-side session context is authoritative. Client tenant, owner,
    # role, entitlement, and session fields are deliberately ignored as authority.
    spec = QueryInterpreter().interpret(data.question)
    plan = build_retrieval_plan(spec)
    _record_audit(db, tenant_id=context["tenant_id"], actor=context["user_id"], action="ASK_QUERY_PROCESSED", correlation_id=correlation_id, details={"status": "INTERPRETED"})
    session.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {
        "status": "INTERPRETED",
        "correlation_id": correlation_id,
        "session_id": str(session.id),
        "user_id": context["user_id"],
        "tenant_id": context["tenant_id"],
        "active_role": context["active_role"],
        "specification": spec.model_dump(mode="json"),
        "retrieval_plan": plan.__dict__,
        "execution": "CONTROLLED_FOUNDATION_ONLY",
        "message": "Question interpreted. Authorized retrieval and model execution are not enabled in this Day 26 foundation.",
    }
