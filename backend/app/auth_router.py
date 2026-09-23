import os
from fastapi import APIRouter, HTTPException, Response, Request, Depends
from pydantic import BaseModel, Field
from auth.service import auth_service, _hash
from auth.emailer import send_password_reset_email, send_verification_email
from backend.app.db.session import get_db
from backend.app.db.models.foundation import AuthUser, Tenant, TenantMembership
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from auth.durable import persist_session, revoke_session, issue_reset, consume
from auth.durable import hash_token
from backend.app.db.models.stage2 import AuthSession
router=APIRouter(prefix="/api/v1/auth",tags=["Authentication"])
class Signup(BaseModel): email:str=Field(min_length=3,max_length=254); password: str=Field(min_length=12,max_length=128); display_name:str=Field(min_length=1,max_length=120); organization:str=Field(min_length=1,max_length=160)
class Signin(BaseModel): email:str; password:str
class Verify(BaseModel): token:str
class ResetRequest(BaseModel): email:str=Field(min_length=3,max_length=254)
class Reset(BaseModel): token:str; password:str=Field(min_length=12,max_length=128)
def fail(exc): return HTTPException(400,detail={"code":str(exc),"message":"Request could not be completed"})
def _development_token(token: str | None) -> str | None:
    return token if os.getenv("MDARIX_ENV", "development").lower() == "development" else None
@router.post('/signup')
def signup(data:Signup, db:Session=Depends(get_db)):
 try:
  if db.query(AuthUser).filter(AuthUser.username==data.email.lower()).first(): raise ValueError("ACCOUNT_EXISTS")
  result=auth_service.signup(data.email,data.password,data.display_name,data.organization); account=auth_service.accounts[data.email.lower()]; tenant=db.query(Tenant).first()
  if not tenant: raise ValueError("TENANT_NOT_CONFIGURED")
  tenant_id=tenant.id; account.tenant_id=str(tenant_id); now=datetime.now(timezone.utc)
  db.add(AuthUser(id=__import__('uuid').uuid4(),tenant_id=tenant_id,username=account.email,display_name=account.display_name,company=data.organization,password_hash=account.password_hash,role=account.role,status=account.status,email_verified=False,created_at=now,updated_at=now)); db.commit()
  result["email_delivery"] = send_verification_email(account.email, result["development_token"])
  return result
 except ValueError as e: raise fail(e)
 except Exception as e: db.rollback(); raise HTTPException(400,detail={"code":"ACCOUNT_CREATE_FAILED","message":"Account could not be created. Check company, email, and password requirements."}) from e
 except ValueError as e: raise fail(e)
@router.post('/verify-email')
def verify(data:Verify, db:Session=Depends(get_db)):
 try:
  result=auth_service.verify_email(data.token); account=next(item for item in auth_service.accounts.values() if item.user_id==result["user_id"]); row=db.query(AuthUser).filter(AuthUser.username==account.email).first()
  if row: row.status="ACTIVE"; row.email_verified=True; row.updated_at=datetime.now(timezone.utc); db.commit()
  return result
 except ValueError as e: raise fail(e)
@router.post('/signin')
def signin(data:Signin,response:Response,db:Session=Depends(get_db)):
 try:
  row=db.query(AuthUser).filter(AuthUser.username==data.email.strip().lower()).first()
  if not row: raise ValueError("INVALID_CREDENTIALS")
  token=auth_service.signin_persisted(data.email,data.password,user_id=row.id,display_name=row.display_name,tenant_id=row.tenant_id,password_hash=row.password_hash,role=row.role,status=row.status,email_verified=row.email_verified)
  persist_session(db, token, row.id, row.tenant_id)
  is_development = os.getenv('MDARIX_ENV','development').lower() == 'development'
  secure_cookie = True if not is_development else os.getenv('MDARIX_COOKIE_SECURE','false').lower() == 'true'
  response.set_cookie('mdarix_session',token,httponly=True,samesite='lax',secure=secure_cookie,max_age=3600); return auth_service.context(token)
 except ValueError as e: raise HTTPException(401,detail={"code":"INVALID_CREDENTIALS","message":"Invalid credentials."}) from e
@router.post('/signout')
def signout(request:Request,response:Response,db:Session=Depends(get_db)):
 token=request.cookies.get('mdarix_session');
 if token: auth_service.signout(token); revoke_session(db, token)
 response.delete_cookie('mdarix_session'); return {"status":"SIGNED_OUT"}
@router.get('/session')
def session(request:Request, db:Session=Depends(get_db)):
 token = request.cookies.get('mdarix_session','')
 row = db.query(AuthSession).filter(AuthSession.session_hash == hash_token(token), AuthSession.revoked_at.is_(None), AuthSession.expires_at > datetime.now(timezone.utc)).first() if token else None
 user = db.query(AuthUser).filter(AuthUser.id == row.user_id, AuthUser.tenant_id == row.tenant_id, AuthUser.status == 'ACTIVE').first() if row else None
 if not user: raise HTTPException(401,detail={"code":"UNAUTHENTICATED","message":"Authentication required"})
 row.last_seen_at = datetime.now(timezone.utc); db.commit()
 return {"user_id":str(user.id),"display_name":user.display_name,"email":user.username,"tenant_id":str(user.tenant_id),"active_role":user.role}
@router.post('/forgot-password')
def forgot(data:ResetRequest, db:Session=Depends(get_db)):
 row=db.query(AuthUser).filter(AuthUser.username==data.email.strip().lower()).first()
 if not row:
  return {"status":"RESET_REQUEST_ACCEPTED","email_delivery":"NOT_SENT"}
 token=issue_reset(db, row.id, row.tenant_id)
 delivery=send_password_reset_email(row.username,token)
 return {"status":"RESET_REQUEST_ACCEPTED","email_delivery":delivery,"development_token": _development_token(token) if delivery=="NOT_CONFIGURED" else None}
@router.post('/reset-password')
def reset(data:Reset, db:Session=Depends(get_db)):
 try:
  user_id=consume(db, data.token, "reset")
  row=db.query(AuthUser).filter(AuthUser.id==user_id).first()
  if row is None: raise ValueError("INVALID_RESET")
  row.password_hash=_hash(data.password); row.status="ACTIVE"; row.email_verified=True; row.updated_at=datetime.now(timezone.utc)
  db.query(TenantMembership).filter(TenantMembership.tenant_id==row.tenant_id,TenantMembership.user_id==row.id).update({"status":"ACTIVE","updated_at":datetime.now(timezone.utc)})
  db.commit()
  return {"status":"PASSWORD_RESET"}
 except ValueError:
  try:return auth_service.reset(data.token,data.password)
  except ValueError as e: raise fail(e)

@router.post('/activate-account')
def activate(data:Reset, db:Session=Depends(get_db)):
 try:
  user_id=consume(db, data.token, "activation")
  row=db.query(AuthUser).filter(AuthUser.id==user_id).first()
  if row is None: raise ValueError("INVALID_ACTIVATION")
  row.password_hash=_hash(data.password); row.status="ACTIVE"; row.email_verified=True; row.updated_at=datetime.now(timezone.utc); db.commit()
  db.query(TenantMembership).filter(TenantMembership.tenant_id==row.tenant_id,TenantMembership.user_id==row.id).update({"status":"ACTIVE","updated_at":datetime.now(timezone.utc)})
  db.commit()
  return {"status":"ACTIVE","user_id":str(row.id),"email":row.username}
 except ValueError as e: raise fail(e)
