import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.evidence.router import get_default_tenant_id
from backend.app.request_context import AuthenticatedRequestContext, get_request_context
from trust_engine.schemas import AssuranceRequest, AssuranceResponse
from trust_engine.service import TrustEngine, TrustError
router=APIRouter(prefix="/api/v1",tags=["AI Trust Assurance"]); service=TrustEngine()
def fail(e): return HTTPException(status_code=404 if e.code.endswith("NOT_FOUND") else 400,detail={"code":e.code,"message":e.message})
@router.post("/ai-executions/{execution_id}/assurance",response_model=AssuranceResponse)
def assure(execution_id:uuid.UUID,request:AssuranceRequest,db:Session=Depends(get_db),ctx:AuthenticatedRequestContext=Depends(get_request_context)):
  try:return service.evaluate(db,ctx.tenant_id,execution_id,request)
  except TrustError as e:raise fail(e) from e
@router.get("/ai-executions/{execution_id}/assurance",response_model=AssuranceResponse)
def get_assurance(execution_id:uuid.UUID,db:Session=Depends(get_db),ctx:AuthenticatedRequestContext=Depends(get_request_context)):
  try:return service.get(db,ctx.tenant_id,execution_id)
  except TrustError as e:raise fail(e) from e
