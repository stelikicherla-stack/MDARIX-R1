import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.request_context import AuthenticatedRequestContext, get_request_context
from auth.service import auth_service
from backend.app.enterprise_audit import make_audit_event
from challenger.schemas import ChallengeRequest, ChallengeResponse
from challenger.service import ChallengerError, ChallengerService
from backend.app.db.models.foundation import Investigation

router=APIRouter(prefix="/api/v1/investigations",tags=["AI Challenger"]); service=ChallengerService()
def _context(request: Request) -> dict:
    try:
        return auth_service.context(request.cookies.get("mdarix_session", ""))
    except ValueError as exc:
        raise HTTPException(status_code=401, detail={"code":"UNAUTHENTICATED","message":"Authentication required"}) from exc
def err(e): return HTTPException(status_code=404 if e.code.endswith("NOT_FOUND") else 400,detail={"code":e.code,"message":e.message})
def _controlled_dependency_failure() -> bool:
    return os.environ.get("DAY31_LIVE_DEPENDENCY_FAILURE") == "1" and os.environ.get("MDARIX_ENV", "development").lower() != "production"
def _authorize_investigation(db: Session, tenant_id: uuid.UUID, investigation_id: uuid.UUID) -> None:
    if db.query(Investigation.id).filter(Investigation.id == investigation_id, Investigation.tenant_id == tenant_id).first() is None:
        raise HTTPException(status_code=404, detail={"code":"INVESTIGATION_NOT_FOUND","message":"Investigation not found"})
@router.post("/{investigation_id}/challenges",response_model=ChallengeResponse)
def create_challenges(investigation_id: uuid.UUID,request: Request, data: ChallengeRequest,db: Session=Depends(get_db), ctx: AuthenticatedRequestContext=Depends(get_request_context)):
    context={"tenant_id":ctx.tenant_id,"user_id":ctx.user_id}; tenant_id=uuid.UUID(ctx.tenant_id); correlation=ctx.correlation_id
    try:
        _authorize_investigation(db, tenant_id, investigation_id)
        if _controlled_dependency_failure():
            raise RuntimeError("controlled Day 31 analysis dependency failure")
        result=service.generate(db,data.model_copy(update={"tenant_id":tenant_id,"investigation_id":investigation_id}))
        db.add(make_audit_event(tenant_id=tenant_id,actor_ref=context["user_id"],action="DAY31_CHALLENGER_EXECUTED",entity_type="Investigation",correlation_id=correlation,details={"result_count":len(result.challenge_set.challenges),"temporal_mode":data.temporal_mode}))
        db.commit()
        return result
    except ChallengerError as e: raise err(e) from e
    except HTTPException:
        raise
    except Exception as exc:
        db.add(make_audit_event(tenant_id=tenant_id,actor_ref=context["user_id"],action="DAY31_DEPENDENCY_FAILED",entity_type="Investigation",correlation_id=correlation,details={"operation":"CHALLENGER","reason":"DEPENDENCY_UNAVAILABLE","temporal_mode":data.temporal_mode}))
        db.commit()
        raise HTTPException(status_code=503,detail={"code":"DEPENDENCY_UNAVAILABLE","message":"Analysis dependency is temporarily unavailable","correlation_id":correlation}) from exc
@router.get("/{investigation_id}/challenges",response_model=ChallengeResponse)
def latest_challenges(investigation_id: uuid.UUID,request: Request,db: Session=Depends(get_db), ctx: AuthenticatedRequestContext=Depends(get_request_context)):
    result=service.latest(db,uuid.UUID(ctx.tenant_id),investigation_id)
    if result is None: raise HTTPException(status_code=404,detail={"code":"CHALLENGE_SET_NOT_FOUND","message":"No challenge set exists"})
    return result
