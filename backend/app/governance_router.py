import hashlib, json, uuid, os
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from auth.service import _verify
from backend.app.db.session import get_db
from backend.app.db.models.foundation import (ApprovalAuthority, AuditEvent, Decision, FeatureEntitlement, PlanDefinition, SegregationOfDutiesPolicy, SignedApprovalRecord, Tenant, TenantPlanAssignment)
from backend.app.db.models.stage3 import ContextSnapshot
from backend.app.request_context import AuthenticatedRequestContext, get_request_context
from backend.app.db.models.foundation import AuthUser
from backend.app.enterprise_audit import change_diff
from backend.app.db.models.stage2 import MfaChallenge
from backend.app.auth_router import _mfa_hash

router=APIRouter(prefix="/api/v1/governance",tags=["Enterprise Governance"])
FEATURE="DECISION_CENTER_SIGNATURES"; ASK_FEATURE="ASK_MDARIX"; NOW=lambda: datetime.now(timezone.utc)
class SignatureRequest(BaseModel):
 decision:str=Field(pattern="^(APPROVE|REJECT)$"); remarks:str=Field(min_length=1,max_length=4000); password:str=Field(min_length=1,max_length=128); object_version:str; mfa_code:str|None=Field(default=None,min_length=6,max_length=12)
class MaterialChangeRequest(BaseModel):
 change_summary:str=Field(min_length=1,max_length=2000); expected_updated_at:str

def audit(db,tenant,actor,action,entity_id,details=None,request=None,reason=None):
 now=NOW(); db.add(AuditEvent(id=uuid.uuid4(),tenant_id=tenant.id,actor_ref=actor,action=action,entity_type="Decision",entity_id=entity_id,details=details or {},source_ip=request.client.host if request and request.client else None,user_agent=request.headers.get("user-agent") if request else None,reason=reason,retention_until=now+__import__('datetime').timedelta(days=365*7),created_at=now))
def bootstrap(db,tenant):
 plan=db.query(PlanDefinition).filter_by(code="R1_GOVERNANCE_DEMO").first()
 now=NOW(); changed=False
 if not plan:
  plan=PlanDefinition(id=uuid.uuid4(),code="R1_GOVERNANCE_DEMO",name="R1 Governance Demo",description="Synthetic non-commercial Day 23 entitlement configuration",version="v1",status="ACTIVE",effective_from=now,effective_to=None,created_at=now,updated_at=now); db.add(plan); db.flush(); changed=True
 for feature in (FEATURE,ASK_FEATURE):
  if not db.query(FeatureEntitlement).filter_by(plan_id=plan.id,feature_code=feature).first():
   db.add(FeatureEntitlement(id=uuid.uuid4(),plan_id=plan.id,feature_code=feature,enabled=True,limits={},status="ACTIVE",created_at=now,updated_at=now)); changed=True
 if not db.query(TenantPlanAssignment).filter_by(tenant_id=tenant.id,plan_id=plan.id).first():
  db.add(TenantPlanAssignment(id=uuid.uuid4(),tenant_id=tenant.id,plan_id=plan.id,status="ACTIVE",effective_from=now,effective_to=None,reason="Day 23 synthetic demo",created_at=now,updated_at=now)); changed=True
 if not db.query(ApprovalAuthority).filter_by(tenant_id=tenant.id,role_name="Viewer",object_type="Decision",decision_type="INVESTIGATION_REVIEW").first():
  db.add(ApprovalAuthority(id=uuid.uuid4(),tenant_id=tenant.id,role_name="Viewer",object_type="Decision",decision_type="INVESTIGATION_REVIEW",scope={},authority="AUTHORIZED",version="v1",status="ACTIVE",effective_from=now,effective_to=None,created_at=now,updated_at=now)); changed=True
 if not db.query(SegregationOfDutiesPolicy).filter_by(tenant_id=tenant.id,object_type="Decision",decision_type="INVESTIGATION_REVIEW").first():
  db.add(SegregationOfDutiesPolicy(id=uuid.uuid4(),tenant_id=tenant.id,name="Decision creator separation",object_type="Decision",decision_type="INVESTIGATION_REVIEW",creator_cannot_approve=True,last_material_editor_cannot_approve=True,version="v1",status="ACTIVE",effective_from=now,effective_to=None,created_at=now,updated_at=now)); changed=True
 if changed: db.commit()
 return plan
def tenant(db,actor):
 try: tenant_id=uuid.UUID(actor["tenant_id"])
 except (ValueError,TypeError): raise HTTPException(403,detail={"code":"TENANT_CONTEXT_INVALID","message":"Authenticated tenant context is invalid"})
 item=db.query(Tenant).filter(Tenant.id==tenant_id,Tenant.status=="active").first()
 if not item: raise HTTPException(403,detail={"code":"TENANT_INACTIVE","message":"Active tenant required"})
 bootstrap(db,item); return item
def entitled(db,t):
 now=NOW(); row=db.query(TenantPlanAssignment).join(PlanDefinition,PlanDefinition.id==TenantPlanAssignment.plan_id).join(FeatureEntitlement,FeatureEntitlement.plan_id==PlanDefinition.id).filter(TenantPlanAssignment.tenant_id==t.id,TenantPlanAssignment.status=="ACTIVE",PlanDefinition.status=="ACTIVE",FeatureEntitlement.feature_code==FEATURE,FeatureEntitlement.enabled==True,FeatureEntitlement.status=="ACTIVE",TenantPlanAssignment.effective_from<=now).first()
 return bool(row)
def session_actor(db, ctx: AuthenticatedRequestContext):
 try:
  user=db.query(AuthUser).filter(AuthUser.id == uuid.UUID(ctx.user_id), AuthUser.tenant_id == ctx.tenant_id).first()
 except (ValueError, TypeError):
  user=None
 if user is None:
  return {"tenant_id":ctx.tenant_id,"user_id":ctx.user_id,"active_role":ctx.active_role_id or "Viewer","display_name":ctx.user_id,"session_id":ctx.session_id}
 return {"tenant_id":ctx.tenant_id,"user_id":ctx.user_id,"active_role":user.role or "Viewer","display_name":user.display_name or ctx.user_id,"session_id":ctx.session_id}
@router.get("/effective-access")
def effective_access(db:Session=Depends(get_db),ctx: AuthenticatedRequestContext=Depends(get_request_context)):
 actor=session_actor(db,ctx); t=tenant(db,actor); return {"feature":FEATURE,"entitled":entitled(db,t),"user_id":actor["user_id"],"active_role":actor["active_role"]}
@router.post("/decisions/{decision_id}/sign")
def sign(decision_id:uuid.UUID,payload:SignatureRequest,request:Request,db:Session=Depends(get_db),ctx: AuthenticatedRequestContext=Depends(get_request_context)):
 actor=session_actor(db,ctx); t=tenant(db,actor); audit(db,t,actor["user_id"],"APPROVAL_REQUESTED",decision_id)
 if not entitled(db,t): audit(db,t,actor["user_id"],"ENTITLEMENT_ACCESS_DENIED",decision_id); db.commit(); raise HTTPException(403,detail={"code":"DENIED_NOT_ENTITLED","message":"Tenant is not entitled to controlled signatures"})
 item=db.query(Decision).filter(Decision.id==decision_id,Decision.tenant_id==t.id).first()
 if not item: raise HTTPException(404,detail={"code":"DECISION_NOT_FOUND","message":"Decision is not available for this tenant"})
 version=item.updated_at.isoformat();
 if payload.object_version!=version: raise HTTPException(409,detail={"code":"STALE_OBJECT_VERSION","message":"Decision changed; re-review the current version"})
 authority=db.query(ApprovalAuthority).filter_by(tenant_id=t.id,role_name=actor["active_role"],object_type="Decision",decision_type="INVESTIGATION_REVIEW",authority="AUTHORIZED",status="ACTIVE").first()
 if not authority: audit(db,t,actor["user_id"],"APPROVAL_AUTHORITY_DENIED",decision_id); db.commit(); raise HTTPException(403,detail={"code":"APPROVAL_AUTHORITY_DENIED","message":"Active role lacks approval authority"})
 sod=db.query(SegregationOfDutiesPolicy).filter_by(tenant_id=t.id,object_type="Decision",decision_type="INVESTIGATION_REVIEW",status="ACTIVE").first()
 if sod and sod.creator_cannot_approve and item.authorized_by_ref==actor["user_id"]: audit(db,t,actor["user_id"],"SOD_DENIED",decision_id); db.commit(); raise HTTPException(403,detail={"code":"SOD_DENIED","message":"Approval by another authorized user is required"})
 if not payload.remarks.strip(): raise HTTPException(400,detail={"code":"REMARKS_REQUIRED","message":"Remarks are required"})
 try:
  user=db.query(AuthUser).filter(AuthUser.id==uuid.UUID(ctx.user_id),AuthUser.tenant_id==ctx.tenant_id).first()
  password_ok = user is not None and _verify(payload.password, user.password_hash)
 except (ValueError, TypeError):
  from auth.service import auth_service
  try: auth_service.verify_current_password(ctx.session_id, payload.password); password_ok = True
  except ValueError: password_ok = False
 if not password_ok: audit(db,t,actor["user_id"],"SIGNATURE_REAUTHENTICATION_FAILED",decision_id); db.commit(); raise HTTPException(403,detail={"code":"INVALID_REAUTHENTICATION","message":"Current password was not verified"})
 user=db.query(AuthUser).filter(AuthUser.id==uuid.UUID(ctx.user_id),AuthUser.tenant_id==ctx.tenant_id).first()
 if os.getenv("MDARIX_REQUIRE_MFA_FOR_SIGNATURES", "false").lower() in {"1","true","yes"}:
  challenge = db.query(MfaChallenge).filter(MfaChallenge.user_id==user.id if user else False, MfaChallenge.tenant_id==t.id, MfaChallenge.purpose=="SIGNATURE", MfaChallenge.used_at.is_(None), MfaChallenge.expires_at>NOW()).order_by(MfaChallenge.created_at.desc()).first() if user else None
  valid_mfa = challenge is not None and payload.mfa_code and hashlib.sha256(payload.mfa_code.encode("ascii")).hexdigest() == challenge.code_hash
  if user is None or not user.mfa_required or not user.mfa_enrolled_at or not valid_mfa:
   audit(db,t,actor["user_id"],"MFA_REQUIRED_FOR_SIGNATURE",decision_id); db.commit(); raise HTTPException(403,detail={"code":"MFA_REQUIRED","message":"MFA enrollment and verification are required for governed signatures"})
  challenge.used_at = NOW()
 material={"decision_id":str(item.id),"version":version,"type":"INVESTIGATION_REVIEW","decision":payload.decision,"remarks":payload.remarks.strip()}; fingerprint=hashlib.sha256(json.dumps(material,sort_keys=True).encode()).hexdigest(); existing=db.query(SignedApprovalRecord).filter_by(tenant_id=t.id,object_type="Decision",object_id=item.id,object_version=version,decision_type="INVESTIGATION_REVIEW").first()
 if existing: raise HTTPException(409,detail={"code":"DUPLICATE_SIGNATURE","message":"This decision version is already signed"})
 meaning=f"I have reviewed this record and {payload.decision.lower()} this decision."; record=SignedApprovalRecord(id=uuid.uuid4(),tenant_id=t.id,object_type="Decision",object_id=item.id,object_version=version,decision_type="INVESTIGATION_REVIEW",decision=payload.decision,remarks=payload.remarks.strip(),signer_user_id=actor["user_id"],signer_role=actor["active_role"],signature_meaning=meaning,content_fingerprint=fingerprint,signature_hash=hashlib.sha256((fingerprint+actor["user_id"]+version).encode()).hexdigest(),status="SIGNED",signed_at=NOW(),created_at=NOW()); db.add(record); item.decision_status="APPROVED" if payload.decision=="APPROVE" else "REJECTED";
 if payload.decision == "APPROVE":
  db.add(ContextSnapshot(id=uuid.uuid4(), tenant_id=t.id, decision_id=item.id, decision_version=version, snapshot={"decision_id":str(item.id),"investigation_id":str(item.investigation_id),"product_id":str(item.product_id) if item.product_id else None,"product_version_id":str(item.product_version_id) if item.product_version_id else None,"selected_action":item.selected_action,"rationale":item.rationale,"approval":payload.remarks}, created_by=actor["user_id"], created_at=NOW()))
 audit(db,t,actor["user_id"],"SIGNED_APPROVAL_CREATED" if payload.decision=="APPROVE" else "SIGNED_REJECTION_CREATED",item.id,{"signature_id":str(record.id),"fingerprint":fingerprint}, request=request, reason=payload.remarks); db.commit(); return {"signature_id":record.id,"status":item.decision_status,"fingerprint":fingerprint,"signer":actor["display_name"],"role":actor["active_role"],"signed_at":record.signed_at}
@router.post("/decisions/{decision_id}/material-change")
def material_change(decision_id:uuid.UUID,payload:MaterialChangeRequest,db:Session=Depends(get_db),ctx: AuthenticatedRequestContext=Depends(get_request_context)):
 actor=session_actor(db,ctx); t=tenant(db,actor); item=db.query(Decision).filter(Decision.id==decision_id,Decision.tenant_id==t.id).first()
 if not item: raise HTTPException(404,detail={"code":"DECISION_NOT_FOUND","message":"Decision is not available for this tenant"})
 current=item.updated_at.isoformat()
 if payload.expected_updated_at!=current: raise HTTPException(409,detail={"code":"STALE_OBJECT_VERSION","message":"Record changed since review"})
 previous = {"decision_status": item.decision_status, "updated_at": current}
 item.updated_at=NOW(); item.decision_status="REQUIRES_REVIEW"; changed_old, changed_new = change_diff(previous, {"decision_status": item.decision_status, "updated_at": item.updated_at.isoformat()}); audit(db,t,actor["user_id"],"RE_REVIEW_REQUIRED",item.id,{"change_summary":payload.change_summary,"previous_version":current,"new_version":item.updated_at.isoformat(),"old_values":changed_old,"new_values":changed_new}); audit(db,t,actor["user_id"],"RE_SIGNATURE_REQUIRED",item.id); db.commit(); return {"status":"RE_REVIEW_REQUIRED","previous_version":current,"current_version":item.updated_at}
@router.get("/decisions/{decision_id}/signature-history")
def signature_history(decision_id:uuid.UUID,db:Session=Depends(get_db),ctx: AuthenticatedRequestContext=Depends(get_request_context)):
 actor=session_actor(db,ctx); t=tenant(db,actor); rows=db.query(SignedApprovalRecord).filter_by(tenant_id=t.id,object_type="Decision",object_id=decision_id).order_by(SignedApprovalRecord.signed_at).all()
 return [{"signature_id":r.id,"object_version":r.object_version,"decision":r.decision,"status":r.status,"signer_user_id":r.signer_user_id,"signer_role":r.signer_role,"signed_at":r.signed_at,"fingerprint":r.content_fingerprint,"signature_meaning":r.signature_meaning} for r in rows]

@router.get("/decisions/{decision_id}/signature-verification")
def signature_verification(decision_id:uuid.UUID,db:Session=Depends(get_db),ctx: AuthenticatedRequestContext=Depends(get_request_context)):
    """Return server-side verification evidence without exposing secrets or signing material."""
    actor=session_actor(db,ctx); t=tenant(db,actor)
    item=db.query(Decision).filter(Decision.id==decision_id,Decision.tenant_id==t.id).first()
    if not item: raise HTTPException(404,detail={"code":"DECISION_NOT_FOUND","message":"Decision is not available for this tenant"})
    rows=db.query(SignedApprovalRecord).filter_by(tenant_id=t.id,object_type="Decision",object_id=decision_id).order_by(SignedApprovalRecord.signed_at).all()
    result=[]
    for r in rows:
        material={"decision_id":str(item.id),"version":r.object_version,"type":r.decision_type,"decision":r.decision,"remarks":r.remarks}
        fingerprint=hashlib.sha256(json.dumps(material,sort_keys=True).encode()).hexdigest()
        expected=hashlib.sha256((fingerprint+r.signer_user_id+r.object_version).encode()).hexdigest()
        result.append({"signature_id":str(r.id),"valid":fingerprint==r.content_fingerprint and expected==r.signature_hash and r.status=="SIGNED","decision":r.decision,"signer_user_id":r.signer_user_id,"signer_role":r.signer_role,"object_version":r.object_version,"signed_at":r.signed_at,"meaning":r.signature_meaning})
    return {"decision_id":str(decision_id),"tenant_id":str(t.id),"verification_status":"VALID" if all(x["valid"] for x in result) and result else "NOT_SIGNED","signatures":result}
