import uuid
from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.evidence.router import get_default_tenant_id
from day14_service import Day14Error,Day14Service
from unknowns.schemas import UnknownRequest,UnknownResponse,UnknownSet
from failure_chain.schemas import FailureChainRequest,FailureChainResponse,FailureChainSet
from unknowns.engine import PROVIDER as U_PROVIDER,ORCHESTRATION_VERSION as U_VERSION
from failure_chain.engine import PROVIDER as F_PROVIDER,ORCHESTRATION_VERSION as F_VERSION

router=APIRouter(prefix="/api/v1/investigations",tags=["Day 14 Intelligence"]); service=Day14Service()
def err(e): return HTTPException(status_code=400,detail={"code":e.code,"message":e.message})
@router.post("/{investigation_id}/unknowns",response_model=UnknownResponse)
def create_unknowns(investigation_id:uuid.UUID,request:UnknownRequest,db:Session=Depends(get_db)):
    try:return service.unknowns(db,request.model_copy(update={"tenant_id":get_default_tenant_id(db),"investigation_id":investigation_id}))
    except Day14Error as e:raise err(e) from e
@router.get("/{investigation_id}/unknowns",response_model=UnknownResponse)
def latest_unknowns(investigation_id:uuid.UUID,db:Session=Depends(get_db)):
    item=service.latest(db,get_default_tenant_id(db),investigation_id,U_PROVIDER,U_VERSION,UnknownSet)
    if not item:raise HTTPException(404,detail={"code":"UNKNOWN_SET_NOT_FOUND","message":"No unknown set exists"})
    result,row=item;return UnknownResponse(unknown_set=result,persisted=True,ai_execution_id=row)
@router.post("/{investigation_id}/failure-chains",response_model=FailureChainResponse)
def create_chains(investigation_id:uuid.UUID,request:FailureChainRequest,db:Session=Depends(get_db)):
    try:return service.chains(db,request.model_copy(update={"tenant_id":get_default_tenant_id(db),"investigation_id":investigation_id}))
    except Day14Error as e:raise err(e) from e
@router.get("/{investigation_id}/failure-chains",response_model=FailureChainResponse)
def latest_chains(investigation_id:uuid.UUID,db:Session=Depends(get_db)):
    item=service.latest(db,get_default_tenant_id(db),investigation_id,F_PROVIDER,F_VERSION,FailureChainSet)
    if not item:raise HTTPException(404,detail={"code":"FAILURE_CHAIN_SET_NOT_FOUND","message":"No failure-chain set exists"})
    result,row=item;return FailureChainResponse(failure_chain_set=result,persisted=True,ai_execution_id=row)
