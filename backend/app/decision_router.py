import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.evidence.router import get_default_tenant_id
from backend.app.db.session import get_db
from decision_center.schemas import AdvisoryRequest, DecisionContextRequest, DecisionCreateRequest, ReviewCreateRequest
from decision_center.service import OPTIONS, DecisionCenterError, DecisionCenterService

router = APIRouter(prefix="/api/v1/investigations", tags=["Decision Center"])
service = DecisionCenterService()


def error(exc: DecisionCenterError) -> HTTPException:
    status = 404 if exc.code.endswith("NOT_FOUND") else 400
    return HTTPException(status_code=status, detail={"code": exc.code, "message": exc.message})


@router.get("/decisions/{decision_id}")
def get_decision(decision_id: uuid.UUID, db: Session = Depends(get_db)):
    from backend.app.db.models.foundation import Decision
    item = db.query(Decision).filter(Decision.tenant_id == get_default_tenant_id(db), Decision.id == decision_id).first()
    if not item:
        raise HTTPException(404, detail={"code": "DECISION_NOT_FOUND", "message": "Decision is not available for this tenant"})
    return _decision_payload(item)


@router.post("/decisions/{decision_id}/reviews")
def review_decision(decision_id: uuid.UUID, request: ReviewCreateRequest, db: Session = Depends(get_db)):
    try:
        review = service.review(db, get_default_tenant_id(db), decision_id, request)
        return {"id": review.id, "decision_id": review.decision_id, "disposition": review.disposition, "reviewer_ref": review.reviewer_ref, "comments": review.comments, "review_timestamp": review.review_timestamp}
    except DecisionCenterError as exc:
        raise error(exc) from exc


@router.get("/{investigation_id}/decision-context")
def decision_context(investigation_id: uuid.UUID, request: DecisionContextRequest = Depends(), db: Session = Depends(get_db)):
    try:
        return service.context(db, get_default_tenant_id(db), investigation_id, request)
    except DecisionCenterError as exc:
        raise error(exc) from exc


@router.post("/{investigation_id}/decision-advisory")
def decision_advisory(investigation_id: uuid.UUID, request: AdvisoryRequest, db: Session = Depends(get_db)):
    try:
        return service.advisory(db, get_default_tenant_id(db), investigation_id, request)
    except DecisionCenterError as exc:
        raise error(exc) from exc


@router.post("/{investigation_id}/decisions")
def create_decision(investigation_id: uuid.UUID, request: DecisionCreateRequest, db: Session = Depends(get_db)):
    if request.selected_action not in OPTIONS:
        raise HTTPException(400, detail={"code": "INVALID_DECISION_OPTION", "message": "Decision option is not controlled"})
    try:
        return _decision_payload(service.create_decision(db, get_default_tenant_id(db), investigation_id, request))
    except DecisionCenterError as exc:
        raise error(exc) from exc


@router.get("/{investigation_id}/decisions")
def list_decisions(investigation_id: uuid.UUID, db: Session = Depends(get_db)):
    from backend.app.db.models.foundation import Decision
    tenant_id = get_default_tenant_id(db)
    service._investigation(db, tenant_id, investigation_id)
    return [_decision_payload(item) for item in db.query(Decision).filter(Decision.tenant_id == tenant_id, Decision.investigation_id == investigation_id).order_by(Decision.decision_timestamp.desc()).all()]


def _decision_payload(item):
    return {"id": item.id, "decision_identifier": item.decision_identifier, "decision_type": item.decision_type, "decision_status": item.decision_status, "decision_readiness": item.decision_readiness, "selected_action": item.selected_action or item.disposition, "human_decision": item.human_decision, "rationale": item.rationale, "authorized_by_ref": item.authorized_by_ref, "decision_timestamp": item.decision_timestamp, "updated_at": item.updated_at, "temporal_context": item.temporal_context, "limitations": item.limitations, "advisory_execution_id": item.advisory_execution_id}
