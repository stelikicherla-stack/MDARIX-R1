import time
from sqlalchemy.orm import Session
from ai.execution import record_ai_execution
from backend.app.db.models.foundation import AIExecution
from hypothesis_engine.service import CompetingHypothesisService
from hypothesis_engine.schemas import HypothesisSetRequest
from challenger.service import ChallengerService
from challenger.schemas import ChallengeRequest
from unknowns.engine import ControlledUnknownsRadar, PROVIDER as U_PROVIDER, MODEL as U_MODEL, ORCHESTRATION_VERSION as U_VERSION
from unknowns.schemas import UnknownRequest, UnknownResponse, UnknownSet
from failure_chain.engine import ControlledFailureChain, PROVIDER as F_PROVIDER, MODEL as F_MODEL, ORCHESTRATION_VERSION as F_VERSION
from failure_chain.schemas import FailureChainRequest, FailureChainResponse, FailureChainSet

class Day14Error(ValueError):
    def __init__(self,code,message): self.code,self.message=code,message
class Day14Service:
    def _inputs(self,db,request):
        hs=CompetingHypothesisService().generate(db,HypothesisSetRequest(tenant_id=request.tenant_id,investigation_id=request.investigation_id,temporal_mode=request.temporal_mode,as_of=request.as_of,persist=True)).hypothesis_set
        cs=ChallengerService().generate(db,ChallengeRequest(tenant_id=request.tenant_id,investigation_id=request.investigation_id,hypothesis_set_id=hs.hypothesis_set_id,temporal_mode=request.temporal_mode,as_of=request.as_of,persist=True)).challenge_set
        return hs,cs
    def unknowns(self,db,request:UnknownRequest):
        if request.tenant_id is None: raise Day14Error("TENANT_REQUIRED","tenant_id is required")
        hs,cs=self._inputs(db,request); started=time.time(); result=ControlledUnknownsRadar().generate(hs,cs); execution=None
        if request.persist:
            row=record_ai_execution(db=db,tenant_id=request.tenant_id,investigation_id=request.investigation_id,provider=U_PROVIDER,model_name=U_MODEL,model_version="1.0",prompt_template_version="R1-Day14-Unknowns-v1",orchestration_version=U_VERSION,context_refs={"context_snapshot_id":result.context_snapshot_id,"context_snapshot_version":result.context_snapshot_version,"source_hypothesis_set_id":str(hs.hypothesis_set_id),"source_challenge_set_id":str(cs.challenge_set_id)},evidence_refs={"unknown_ids":[str(u.unknown_id) for u in result.unknowns]},structured_input=request.model_dump(mode="json"),structured_output=result.model_dump(mode="json"),validation_status="COMPLETED",latency_ms=int((time.time()-started)*1000),requestor_ref="MDARIX-Unknowns-Radar"); db.commit(); execution=row.id
        return UnknownResponse(unknown_set=result,persisted=request.persist,ai_execution_id=execution)
    def chains(self,db,request:FailureChainRequest):
        if request.tenant_id is None: raise Day14Error("TENANT_REQUIRED","tenant_id is required")
        hs,cs=self._inputs(db,request); us=ControlledUnknownsRadar().generate(hs,cs); started=time.time(); result=ControlledFailureChain().generate(hs,us); execution=None
        if request.persist:
            row=record_ai_execution(db=db,tenant_id=request.tenant_id,investigation_id=request.investigation_id,provider=F_PROVIDER,model_name=F_MODEL,model_version="1.0",prompt_template_version="R1-Day14-FailureChain-v1",orchestration_version=F_VERSION,context_refs={"context_snapshot_id":result.context_snapshot_id,"context_snapshot_version":result.context_snapshot_version,"source_hypothesis_set_id":str(hs.hypothesis_set_id),"source_unknown_set_id":str(us.unknown_set_id)},evidence_refs={"chain_ids":[str(c.chain_id) for c in result.chains]},structured_input=request.model_dump(mode="json"),structured_output=result.model_dump(mode="json"),validation_status="COMPLETED",latency_ms=int((time.time()-started)*1000),requestor_ref="MDARIX-Failure-Chain"); db.commit(); execution=row.id
        return FailureChainResponse(failure_chain_set=result,persisted=request.persist,ai_execution_id=execution)
    def latest(self,db,tenant_id,investigation_id,provider,version,model):
        row=db.query(AIExecution).filter(AIExecution.tenant_id==tenant_id,AIExecution.investigation_id==investigation_id,AIExecution.provider==provider,AIExecution.orchestration_version==version).order_by(AIExecution.execution_timestamp.desc()).first()
        if not row or not row.structured_output: return None
        return model.model_validate(row.structured_output),row.id
