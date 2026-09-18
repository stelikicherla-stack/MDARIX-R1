"""Authenticated, non-chat Ask MDARIX control-plane endpoint."""
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ask_mdarix import QueryInterpreter
from auth.service import auth_service
from backend.app.db.models.foundation import Tenant
from backend.app.db.session import get_db

router = APIRouter(prefix="/api/v1/ask", tags=["Ask MDARIX"])


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


@router.post("/")
def ask(request: Request, data: AskRequest, db: Session = Depends(get_db)) -> dict:
    context = _authenticated_context(request)
    tenant = db.query(Tenant).filter(Tenant.id == context["tenant_id"]).first()
    if tenant is None or str(tenant.status).lower() not in {"active", "enabled"}:
        raise HTTPException(status_code=403, detail={"code": "TENANT_UNAVAILABLE", "message": "Tenant is not available"})

    # The server-side session context is authoritative. Client tenant, role,
    # entitlement, and session fields are deliberately ignored as authority.
    spec = QueryInterpreter().interpret(data.question)
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid4())
    return {
        "status": "INTERPRETED",
        "correlation_id": correlation_id,
        "user_id": context["user_id"],
        "tenant_id": context["tenant_id"],
        "active_role": context["active_role"],
        "specification": spec.model_dump(mode="json"),
        "execution": "CONTROLLED_FOUNDATION_ONLY",
        "message": "Question interpreted. Authorized retrieval and model execution are not enabled in this Day 26 foundation.",
    }
