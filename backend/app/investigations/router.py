import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.evidence.router import get_default_tenant_id
from investigation_workspace.schemas import InvestigationWorkspaceRequest, InvestigationWorkspaceResponse
from investigation_workspace.service import InvestigationWorkspaceError, InvestigationWorkspaceService


router = APIRouter(prefix="/api/v1/investigations", tags=["Investigation Workspace"])
service = InvestigationWorkspaceService()


def workspace_error(exc: InvestigationWorkspaceError) -> HTTPException:
    status = 404 if exc.code == "INVESTIGATION_NOT_FOUND" else 400
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
