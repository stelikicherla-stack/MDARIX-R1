import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.evidence.router import get_default_tenant_id
from briefs.schemas import BriefCreateRequest, BriefListResponse, BriefResponse
from briefs.service import BriefError, BriefService
from auth.service import auth_service

router = APIRouter(prefix="/api/v1/investigations", tags=["Investigation Brief"])
service = BriefService()

def tenant_context(request: Request, db: Session):
    token = request.cookies.get("mdarix_session", "")
    if token:
        try:
            return auth_service.context(token)
        except ValueError as exc:
            raise HTTPException(status_code=401, detail={"code": "UNAUTHENTICATED", "message": "Authentication required"}) from exc
    return {"tenant_id": str(get_default_tenant_id(db)), "user_id": "SYSTEM"}

def err(exc: BriefError):
    return HTTPException(status_code=404 if exc.code.endswith("NOT_FOUND") else 400, detail={"code": exc.code, "message": exc.message})

@router.post("/{investigation_id}/briefs", response_model=BriefResponse)
def generate_brief(investigation_id: uuid.UUID, request: BriefCreateRequest, http_request: Request, db: Session = Depends(get_db)):
    try:
        context = tenant_context(http_request, db); request.generated_by = context["user_id"]
        return service.generate(db, uuid.UUID(context["tenant_id"]), investigation_id, request)
    except BriefError as exc: raise err(exc) from exc

@router.get("/{investigation_id}/briefs", response_model=BriefListResponse)
def list_briefs(investigation_id: uuid.UUID, http_request: Request, db: Session = Depends(get_db)):
    try: return {"briefs": service.list(db, uuid.UUID(tenant_context(http_request, db)["tenant_id"]), investigation_id)}
    except BriefError as exc: raise err(exc) from exc

@router.get("/{investigation_id}/briefs/latest", response_model=BriefResponse)
def latest_brief(investigation_id: uuid.UUID, http_request: Request, db: Session = Depends(get_db)):
    try: return service.get(db, uuid.UUID(tenant_context(http_request, db)["tenant_id"]), investigation_id, latest=True)
    except BriefError as exc: raise err(exc) from exc

@router.get("/{investigation_id}/briefs/{brief_id}", response_model=BriefResponse)
def get_brief(investigation_id: uuid.UUID, brief_id: uuid.UUID, http_request: Request, db: Session = Depends(get_db)):
    try: return service.get(db, uuid.UUID(tenant_context(http_request, db)["tenant_id"]), investigation_id, brief_id=brief_id)
    except BriefError as exc: raise err(exc) from exc
