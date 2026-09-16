import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.evidence.router import get_default_tenant_id
from investigation_workspace.schemas import InvestigationWorkspaceRequest, InvestigationWorkspaceResponse
from investigation_workspace.service import InvestigationWorkspaceError, InvestigationWorkspaceService
from investigator.schemas import InvestigationAnalysisRequest, InvestigationAnalysisResponse
from investigator.service import EvidenceGroundedInvestigatorService, InvestigatorError


router = APIRouter(prefix="/api/v1/investigations", tags=["Investigation Workspace"])
service = InvestigationWorkspaceService()
investigator_service = EvidenceGroundedInvestigatorService()


def workspace_error(exc: InvestigationWorkspaceError) -> HTTPException:
    status = 404 if exc.code == "INVESTIGATION_NOT_FOUND" else 400
    return HTTPException(status_code=status, detail={"code": exc.code, "message": exc.message})


def investigator_error(exc: InvestigatorError) -> HTTPException:
    status = 404 if exc.code in {"INVESTIGATION_NOT_FOUND", "ANALYSIS_NOT_FOUND"} else 400
    return HTTPException(status_code=status, detail={"code": exc.code, "message": exc.message})


@router.get("/{investigation_id}/workspace", response_model=InvestigationWorkspaceResponse)
def get_investigation_workspace(
    investigation_id: uuid.UUID,
    temporal_mode: str = Query("current", pattern="^(current|event|known)$"),
    as_of: datetime | None = None,
    include_retrieval: bool = True,
    retrieval_top_k: int = Query(8, ge=1, le=25),
    db: Session = Depends(get_db),
) -> InvestigationWorkspaceResponse:
    tenant_id = get_default_tenant_id(db)
    request = InvestigationWorkspaceRequest(
        tenant_id=tenant_id,
        investigation_id=investigation_id,
        temporal_mode=temporal_mode,
        as_of=as_of,
        include_retrieval=include_retrieval,
        retrieval_top_k=retrieval_top_k,
    )
    try:
        return service.workspace(db, request)
    except InvestigationWorkspaceError as exc:
        raise workspace_error(exc) from exc


@router.post("/{investigation_id}/analysis", response_model=InvestigationAnalysisResponse)
def create_investigation_analysis(
    investigation_id: uuid.UUID,
    request: InvestigationAnalysisRequest,
    db: Session = Depends(get_db),
) -> InvestigationAnalysisResponse:
    tenant_id = get_default_tenant_id(db)
    scoped_request = request.model_copy(update={"tenant_id": tenant_id, "investigation_id": investigation_id})
    try:
        return investigator_service.analyze(db, scoped_request)
    except InvestigatorError as exc:
        raise investigator_error(exc) from exc


@router.get("/{investigation_id}/analysis/latest", response_model=InvestigationAnalysisResponse)
def get_latest_investigation_analysis(
    investigation_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> InvestigationAnalysisResponse:
    tenant_id = get_default_tenant_id(db)
    result = investigator_service.latest(db, tenant_id, investigation_id)
    if result is None:
        raise HTTPException(status_code=404, detail={"code": "ANALYSIS_NOT_FOUND", "message": "No investigation analysis exists"})
    return result


@router.get("/{investigation_id}/analysis/{analysis_id}", response_model=InvestigationAnalysisResponse)
def get_investigation_analysis(
    investigation_id: uuid.UUID,
    analysis_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> InvestigationAnalysisResponse:
    tenant_id = get_default_tenant_id(db)
    try:
        return investigator_service.get(db, tenant_id, investigation_id, analysis_id)
    except InvestigatorError as exc:
        raise investigator_error(exc) from exc
