import hashlib, json, re, uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.app.db.models.foundation import AIExecution, AssuranceResult, AssuranceCheck, Evidence, ProductVersion
class TrustError(ValueError):
    def __init__(self, code, message): self.code, self.message = code, message
POLICY="MDARIX_AI_TRUST_POLICY_R1_V1"
class TrustEngine:
  def _payload(self, result, checks):
    return {"id":result.id,"ai_execution_id":result.ai_execution_id,"status":result.status,"assurance_version":result.assurance_version,"trust_policy_version":result.trust_policy_version,"human_review_required":result.human_review_required,"revalidation_required":result.revalidation_required,"configuration_hash":result.configuration_hash,"checks":[{"check_type":c.check_type,"status":c.status,"severity":c.severity,"message":c.message,"details":c.details} for c in checks],"limitations":result.limitations,"generated_at":result.generated_at}
  def evaluate(self, db: Session, tenant_id: uuid.UUID, execution_id: uuid.UUID, request):
    ex=db.query(AIExecution).filter(AIExecution.tenant_id==tenant_id,AIExecution.id==execution_id).first()
    if not ex: raise TrustError("AI_EXECUTION_NOT_FOUND","AI execution is not available for this tenant")
    out=ex.structured_output or {}; refs=(ex.evidence_refs or {}).get("evidence_identifiers",[]) if isinstance(ex.evidence_refs,dict) else []
    checks=[]; now=datetime.now(timezone.utc)
    def add(t,s,sev,m,d=None): checks.append((t,s,sev,m,d or {}))
    evs=db.query(Evidence).filter(Evidence.tenant_id==tenant_id,Evidence.investigation_id==ex.investigation_id).all(); ids={e.evidence_identifier for e in evs}
    missing=[str(x) for x in refs if str(x) not in ids and x]
    add("EVIDENCE_GROUNDING","BLOCKED" if missing else "PASS","CRITICAL" if missing else "INFO","Referenced evidence resolves." if not missing else f"Nonexistent evidence citations: {missing}",{"missing":missing})
    text=json.dumps(out).lower(); unsafe=bool(re.search(r"(root cause confirmed|caused by|proven cause|definitely responsible|mdarix approves|ai approves|approved the investigation|recall required|capa required)",text))
    add("UNSUPPORTED_CLAIMS","BLOCKED" if unsafe else "PASS","HIGH" if unsafe else "INFO","Potential unsupported causal or human-authority claim detected." if unsafe else "No restricted claim wording detected.")
    add("CAUSALITY_RESTRAINT","BLOCKED" if unsafe else "PASS","HIGH" if unsafe else "INFO","Causality is not established by this deterministic check." )
    add("TENANT_INTEGRITY","PASS","INFO","AIExecution and referenced records are tenant-scoped.")
    add("PROVENANCE","PASS" if ex.provider and ex.model_name and ex.execution_timestamp else "BLOCKED","CRITICAL" if not ex.provider or not ex.model_name else "INFO","Execution provenance is present." if ex.provider and ex.model_name and ex.execution_timestamp else "Required execution provenance is incomplete.")
    cfg={"provider":ex.provider,"model":ex.model_name,"model_version":ex.model_version,"prompt":ex.prompt_template_version,"policy":POLICY}; digest=hashlib.sha256(json.dumps(cfg,sort_keys=True).encode()).hexdigest()
    blocked=any(c[1]=="BLOCKED" for c in checks); status="BLOCKED" if blocked else "PASS_WITH_LIMITATIONS" if not ex.evidence_refs else "PASS"
    result=AssuranceResult(id=uuid.uuid4(),tenant_id=tenant_id,investigation_id=ex.investigation_id,ai_execution_id=ex.id,output_type=request.output_type,output_id=request.output_id,assurance_version=1,status=status,generated_at=now,trust_policy_version=POLICY,temporal_mode=(ex.context_refs or {}).get("temporal_mode") if isinstance(ex.context_refs,dict) else None,temporal_cutoff=None,human_review_required=True,revalidation_required=False,limitations={"items":["Assurance PASS does not mean the AI conclusion is objectively true."]},configuration_hash=digest,created_at=now); db.add(result); db.flush()
    rows=[]
    for t,s,sev,m,d in checks: row=AssuranceCheck(id=uuid.uuid4(),tenant_id=tenant_id,assurance_result_id=result.id,check_type=t,status=s,severity=sev,message=m,details=d,created_at=now); db.add(row); rows.append(row)
    db.commit(); return self._payload(result,rows)
  def get(self,db,tenant_id,execution_id):
    r=db.query(AssuranceResult).filter(AssuranceResult.tenant_id==tenant_id,AssuranceResult.ai_execution_id==execution_id).order_by(AssuranceResult.created_at.desc()).first()
    if not r: raise TrustError("ASSURANCE_NOT_FOUND","No assurance result exists")
    return self._payload(r,db.query(AssuranceCheck).filter(AssuranceCheck.tenant_id==tenant_id,AssuranceCheck.assurance_result_id==r.id).all())
