from fastapi import APIRouter, HTTPException, Response, Request, Depends
from pydantic import BaseModel, Field
from auth.service import auth_service
from backend.app.db.session import get_db
from backend.app.db.models.foundation import AuthUser, Tenant
from sqlalchemy.orm import Session
from datetime import datetime, timezone
router=APIRouter(prefix="/api/v1/auth",tags=["Authentication"])
class Signup(BaseModel): email:str=Field(min_length=3,max_length=254); password: str=Field(min_length=12,max_length=128); display_name:str=Field(min_length=1,max_length=120); organization:str=Field(min_length=1,max_length=160)
class Signin(BaseModel): email:str; password:str
class Verify(BaseModel): token:str
class ResetRequest(BaseModel): email:str=Field(min_length=3,max_length=254)
class Reset(BaseModel): token:str; password:str=Field(min_length=12,max_length=128)
def fail(exc): return HTTPException(400,detail={"code":str(exc),"message":"Request could not be completed"})
@router.post('/signup')
def signup(data:Signup, db:Session=Depends(get_db)):
 try:
  result=auth_service.signup(data.email,data.password,data.display_name,data.organization); account=auth_service.accounts[data.email.lower()]; tenant=db.query(Tenant).first()
  if not tenant: raise ValueError("TENANT_NOT_CONFIGURED")
  tenant_id=tenant.id; now=datetime.now(timezone.utc)
  db.add(AuthUser(id=__import__('uuid').uuid4(),tenant_id=tenant_id,username=account.email,display_name=account.display_name,company=data.organization,password_hash=account.password_hash,role=account.role,status=account.status,email_verified=False,created_at=now,updated_at=now)); db.commit(); return result
 except ValueError as e: raise fail(e)
 except Exception as e: db.rollback(); raise HTTPException(400,detail={"code":"ACCOUNT_CREATE_FAILED","message":"Account could not be created. Check the form and try again."}) from e
 except ValueError as e: raise fail(e)
@router.post('/verify-email')
def verify(data:Verify):
 try:return auth_service.verify_email(data.token)
 except ValueError as e: raise fail(e)
@router.post('/signin')
def signin(data:Signin,response:Response):
 try:
  token=auth_service.signin(data.email,data.password); response.set_cookie('mdarix_session',token,httponly=True,samesite='lax',secure=False,max_age=3600); return auth_service.context(token)
 except ValueError as e: raise HTTPException(401,detail={"code":"INVALID_CREDENTIALS","message":"Invalid credentials."}) from e
@router.post('/signout')
def signout(request:Request,response:Response):
 token=request.cookies.get('mdarix_session');
 if token: auth_service.signout(token)
 response.delete_cookie('mdarix_session'); return {"status":"SIGNED_OUT"}
@router.get('/session')
def session(request:Request):
 try:return auth_service.context(request.cookies.get('mdarix_session',''))
 except ValueError as e: raise HTTPException(401,detail={"code":"UNAUTHENTICATED","message":"Authentication required"}) from e
@router.post('/forgot-password')
def forgot(data:ResetRequest): return auth_service.request_reset(data.email)
@router.post('/reset-password')
def reset(data:Reset):
 try:return auth_service.reset(data.token,data.password)
 except ValueError as e: raise fail(e)
