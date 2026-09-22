import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.request_context import AuthenticatedRequestContext, get_request_context
from briefs.schemas import BriefCreateRequest, BriefListResponse, BriefResponse
from briefs.service import BriefError, BriefService

router = APIRouter(prefix="/api/v1/investigations", tags=["Investigation Brief"])
service = BriefService()

def err(exc: BriefError):
    return HTTPException(status_code=404 if exc.code.endswith("NOT_FOUND") else 400, detail={"code": exc.code, "message": exc.message})

@router.post("/{investigation_id}/briefs", response_model=BriefResponse)
def generate_brief(investigation_id: uuid.UUID, request: BriefCreateRequest, db: Session = Depends(get_db), ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    try:
        request.generated_by = ctx.user_id
        return service.generate(db, uuid.UUID(ctx.tenant_id), investigation_id, request)
    except BriefError as exc: raise err(exc) from exc

@router.get("/{investigation_id}/briefs", response_model=BriefListResponse)
def list_briefs(investigation_id: uuid.UUID, db: Session = Depends(get_db), ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    try: return {"briefs": service.list(db, uuid.UUID(ctx.tenant_id), investigation_id)}
    except BriefError as exc: raise err(exc) from exc

@router.get("/{investigation_id}/briefs/latest", response_model=BriefResponse)
def latest_brief(investigation_id: uuid.UUID, db: Session = Depends(get_db), ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    try: return service.get(db, uuid.UUID(ctx.tenant_id), investigation_id, latest=True)
    except BriefError as exc: raise err(exc) from exc

@router.get("/{investigation_id}/briefs/{brief_id}", response_model=BriefResponse)
def get_brief(investigation_id: uuid.UUID, brief_id: uuid.UUID, db: Session = Depends(get_db), ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    try: return service.get(db, uuid.UUID(ctx.tenant_id), investigation_id, brief_id=brief_id)
    except BriefError as exc: raise err(exc) from exc
