import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.evidence.router import get_default_tenant_id
from briefs.schemas import BriefCreateRequest, BriefListResponse, BriefResponse
from briefs.service import BriefError, BriefService

router = APIRouter(prefix="/api/v1/investigations", tags=["Investigation Brief"])
service = BriefService()

def err(exc: BriefError):
    return HTTPException(status_code=404 if exc.code.endswith("NOT_FOUND") else 400, detail={"code": exc.code, "message": exc.message})

@router.post("/{investigation_id}/briefs", response_model=BriefResponse)
def generate_brief(investigation_id: uuid.UUID, request: BriefCreateRequest, db: Session = Depends(get_db)):
    try: return service.generate(db, get_default_tenant_id(db), investigation_id, request)
    except BriefError as exc: raise err(exc) from exc

@router.get("/{investigation_id}/briefs", response_model=BriefListResponse)
def list_briefs(investigation_id: uuid.UUID, db: Session = Depends(get_db)):
    try: return {"briefs": service.list(db, get_default_tenant_id(db), investigation_id)}
    except BriefError as exc: raise err(exc) from exc

@router.get("/{investigation_id}/briefs/latest", response_model=BriefResponse)
def latest_brief(investigation_id: uuid.UUID, db: Session = Depends(get_db)):
    try: return service.get(db, get_default_tenant_id(db), investigation_id, latest=True)
    except BriefError as exc: raise err(exc) from exc

@router.get("/{investigation_id}/briefs/{brief_id}", response_model=BriefResponse)
def get_brief(investigation_id: uuid.UUID, brief_id: uuid.UUID, db: Session = Depends(get_db)):
    try: return service.get(db, get_default_tenant_id(db), investigation_id, brief_id=brief_id)
    except BriefError as exc: raise err(exc) from exc
