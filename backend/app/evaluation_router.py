import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.evidence.router import get_default_tenant_id
from backend.app.request_context import AuthenticatedRequestContext, get_request_context
from backend.app.db.models.foundation import EvaluationRun, ReleaseAssuranceResult
from evaluation.harness import configuration_snapshot, run_golden_suite
router=APIRouter(prefix="/api/v1/evaluations",tags=["Golden Evaluation"])
class EvaluationRequest(BaseModel): release_version: str="MDARIX-R1"; model_version: str="1.0"; prompt_version: str="R1-controlled-v1"
@router.post("/runs")
def run_evaluation(request:EvaluationRequest,db:Session=Depends(get_db),ctx:AuthenticatedRequestContext=Depends(get_request_context)):
 tenant=ctx.tenant_id; started=datetime.now(timezone.utc); snap=configuration_snapshot(model_version=request.model_version,prompt_version=request.prompt_version); result=run_golden_suite(snap); now=datetime.now(timezone.utc); row=EvaluationRun(id=uuid.uuid4(),tenant_id=tenant,suite_version=result["suite_version"],dataset_version=result["dataset_version"],release_version=request.release_version,configuration_hash=result["configuration_hash"],status=result["status"],results=result,started_at=started,completed_at=now,created_at=now); db.add(row); db.flush(); assurance=ReleaseAssuranceResult(id=uuid.uuid4(),tenant_id=tenant,evaluation_run_id=row.id,release_version=request.release_version,suite_version=result["suite_version"],dataset_version=result["dataset_version"],configuration_hash=result["configuration_hash"],status="PASS" if result["status"]=="PASS" else "BLOCKED",critical_failures={"items":result["critical_failures"]},limitations={"items":["Internal assurance only; not regulatory certification."]},generated_at=now,created_at=now); db.add(assurance); db.commit(); return {"evaluation_run_id":row.id,"release_assurance_id":assurance.id,**result,"release_assurance_status":assurance.status,"review_status":assurance.review_status}
@router.get("/runs/{run_id}")
def get_evaluation(run_id:uuid.UUID,db:Session=Depends(get_db),ctx:AuthenticatedRequestContext=Depends(get_request_context)):
 tenant=ctx.tenant_id; row=db.query(EvaluationRun).filter(EvaluationRun.tenant_id==tenant,EvaluationRun.id==run_id).first()
 if not row: raise HTTPException(404,detail={"code":"EVALUATION_NOT_FOUND","message":"Evaluation run is not available for this tenant"})
 return {"evaluation_run_id":row.id,"suite_version":row.suite_version,"dataset_version":row.dataset_version,"release_version":row.release_version,"configuration_hash":row.configuration_hash,"status":row.status,"results":row.results}
