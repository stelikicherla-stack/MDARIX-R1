import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.evidence.router import get_default_tenant_id
from backend.app.request_context import AuthenticatedRequestContext, get_request_context
from .schemas import CounterfactualRequest, CounterfactualResponse
from .service import CounterfactualError, CounterfactualService

router = APIRouter(prefix="/api/v1/investigations", tags=["Day 16 Counterfactual"])
service = CounterfactualService()


def payload(item) -> CounterfactualResponse:
    return CounterfactualResponse(id=item.id, investigation_id=item.investigation_id, status=item.status, result=item.assumptions["result"], created_at=item.created_at)


@router.post("/{investigation_id}/counterfactuals", response_model=CounterfactualResponse)
def create_counterfactual(investigation_id: uuid.UUID, request: CounterfactualRequest, db: Session = Depends(get_db), ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    try:
        return payload(service.execute(db, ctx.tenant_id, investigation_id, request))
    except CounterfactualError as exc:
        raise HTTPException(404 if exc.code.endswith("NOT_FOUND") else 400, detail={"code": exc.code, "message": exc.message}) from exc


@router.get("/{investigation_id}/counterfactuals", response_model=list[CounterfactualResponse])
def list_counterfactuals(investigation_id: uuid.UUID, db: Session = Depends(get_db), ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    return [payload(item) for item in service.list(db, ctx.tenant_id, investigation_id)]


@router.get("/counterfactuals/{counterfactual_id}", response_model=CounterfactualResponse)
def get_counterfactual(counterfactual_id: uuid.UUID, db: Session = Depends(get_db), ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    from backend.app.db.models.foundation import Scenario
    item = db.query(Scenario).filter(Scenario.tenant_id == ctx.tenant_id, Scenario.id == counterfactual_id, Scenario.assumptions["kind"].astext == "COUNTERFACTUAL").first()
    if not item:
        raise HTTPException(404, detail={"code": "COUNTERFACTUAL_NOT_FOUND", "message": "Counterfactual is not available for this tenant"})
    return payload(item)
