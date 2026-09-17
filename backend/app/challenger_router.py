import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.evidence.router import get_default_tenant_id
from challenger.schemas import ChallengeRequest, ChallengeResponse
from challenger.service import ChallengerError, ChallengerService

router=APIRouter(prefix="/api/v1/investigations",tags=["AI Challenger"]); service=ChallengerService()
def err(e): return HTTPException(status_code=404 if e.code.endswith("NOT_FOUND") else 400,detail={"code":e.code,"message":e.message})
@router.post("/{investigation_id}/challenges",response_model=ChallengeResponse)
def create_challenges(investigation_id: uuid.UUID,request: ChallengeRequest,db: Session=Depends(get_db)):
    try: return service.generate(db,request.model_copy(update={"tenant_id":get_default_tenant_id(db),"investigation_id":investigation_id}))
    except ChallengerError as e: raise err(e) from e
@router.get("/{investigation_id}/challenges",response_model=ChallengeResponse)
def latest_challenges(investigation_id: uuid.UUID,db: Session=Depends(get_db)):
    result=service.latest(db,get_default_tenant_id(db),investigation_id)
    if result is None: raise HTTPException(status_code=404,detail={"code":"CHALLENGE_SET_NOT_FOUND","message":"No challenge set exists"})
    return result
