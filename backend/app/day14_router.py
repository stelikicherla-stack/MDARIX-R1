import os
import uuid
from fastapi import APIRouter,Depends,HTTPException,Request
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.request_context import AuthenticatedRequestContext, get_request_context
from auth.service import auth_service
from backend.app.enterprise_audit import make_audit_event
from day14_service import Day14Error,Day14Service
from unknowns.schemas import UnknownRequest,UnknownResponse,UnknownSet
from failure_chain.schemas import FailureChainRequest,FailureChainResponse,FailureChainSet
from unknowns.engine import PROVIDER as U_PROVIDER,ORCHESTRATION_VERSION as U_VERSION
from failure_chain.engine import PROVIDER as F_PROVIDER,ORCHESTRATION_VERSION as F_VERSION
from backend.app.db.models.foundation import Investigation

router=APIRouter(prefix="/api/v1/investigations",tags=["Day 14 Intelligence"]); service=Day14Service()
def _context(request: Request) -> dict:
    try:
        return auth_service.context(request.cookies.get("mdarix_session", ""))
    except ValueError as exc:
        raise HTTPException(status_code=401, detail={"code":"UNAUTHENTICATED","message":"Authentication required"}) from exc
def err(e): return HTTPException(status_code=400,detail={"code":e.code,"message":e.message})
def _controlled_dependency_failure() -> bool:
    return os.environ.get("DAY31_LIVE_DEPENDENCY_FAILURE") == "1" and os.environ.get("MDARIX_ENV", "development").lower() != "production"
def _authorize_investigation(db: Session, tenant_id: uuid.UUID, investigation_id: uuid.UUID) -> None:
    if db.query(Investigation.id).filter(Investigation.id == investigation_id, Investigation.tenant_id == tenant_id).first() is None:
        raise HTTPException(status_code=404, detail={"code":"INVESTIGATION_NOT_FOUND","message":"Investigation not found"})
@router.post("/{investigation_id}/unknowns",response_model=UnknownResponse)
def create_unknowns(investigation_id:uuid.UUID,request:Request,data:UnknownRequest,db:Session=Depends(get_db),ctx:AuthenticatedRequestContext=Depends(get_request_context)):
    try:return service.unknowns(db,data.model_copy(update={"tenant_id":uuid.UUID(ctx.tenant_id),"investigation_id":investigation_id}))
    except Day14Error as e:raise err(e) from e
@router.get("/{investigation_id}/unknowns",response_model=UnknownResponse)
def latest_unknowns(investigation_id:uuid.UUID,request:Request,db:Session=Depends(get_db),ctx:AuthenticatedRequestContext=Depends(get_request_context)):
    item=service.latest(db,uuid.UUID(ctx.tenant_id),investigation_id,U_PROVIDER,U_VERSION,UnknownSet)
    if not item:raise HTTPException(404,detail={"code":"UNKNOWN_SET_NOT_FOUND","message":"No unknown set exists"})
    result,row=item;return UnknownResponse(unknown_set=result,persisted=True,ai_execution_id=row)
@router.post("/{investigation_id}/failure-chains",response_model=FailureChainResponse)
def create_chains(investigation_id:uuid.UUID,request:Request,data:FailureChainRequest,db:Session=Depends(get_db),ctx:AuthenticatedRequestContext=Depends(get_request_context)):
    context={"tenant_id":ctx.tenant_id,"user_id":ctx.user_id}; tenant_id=uuid.UUID(ctx.tenant_id); correlation=ctx.correlation_id
    try:
        _authorize_investigation(db, tenant_id, investigation_id)
        if _controlled_dependency_failure():
            raise RuntimeError("controlled Day 31 analysis dependency failure")
        result=service.chains(db,data.model_copy(update={"tenant_id":tenant_id,"investigation_id":investigation_id}))
        db.add(make_audit_event(tenant_id=tenant_id,actor_ref=context["user_id"],action="DAY31_FAILURE_CHAIN_EXECUTED",entity_type="Investigation",correlation_id=correlation,details={"result_count":len(result.failure_chain_set.chains),"temporal_mode":data.temporal_mode}))
        db.commit()
        return result
    except Day14Error as e:raise err(e) from e
    except HTTPException:
        raise
    except Exception as exc:
        db.add(make_audit_event(tenant_id=tenant_id,actor_ref=context["user_id"],action="DAY31_DEPENDENCY_FAILED",entity_type="Investigation",correlation_id=correlation,details={"operation":"FAILURE_CHAIN","reason":"DEPENDENCY_UNAVAILABLE","temporal_mode":data.temporal_mode}))
        db.commit()
        raise HTTPException(status_code=503,detail={"code":"DEPENDENCY_UNAVAILABLE","message":"Analysis dependency is temporarily unavailable","correlation_id":correlation}) from exc
@router.get("/{investigation_id}/failure-chains",response_model=FailureChainResponse)
def latest_chains(investigation_id:uuid.UUID,request:Request,db:Session=Depends(get_db),ctx:AuthenticatedRequestContext=Depends(get_request_context)):
    item=service.latest(db,uuid.UUID(ctx.tenant_id),investigation_id,F_PROVIDER,F_VERSION,FailureChainSet)
    if not item:raise HTTPException(404,detail={"code":"FAILURE_CHAIN_SET_NOT_FOUND","message":"No failure-chain set exists"})
    result,row=item;return FailureChainResponse(failure_chain_set=result,persisted=True,ai_execution_id=row)
