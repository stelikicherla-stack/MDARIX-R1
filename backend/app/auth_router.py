from fastapi import APIRouter, HTTPException, Response, Request
from pydantic import BaseModel, Field
from auth.service import auth_service
router=APIRouter(prefix="/api/v1/auth",tags=["Authentication"])
class Signup(BaseModel): email:str=Field(min_length=3,max_length=254); password: str=Field(min_length=12,max_length=128); display_name:str=Field(min_length=1,max_length=120); organization:str=Field(min_length=1,max_length=160)
class Signin(BaseModel): email:str; password:str
class Verify(BaseModel): token:str
class ResetRequest(BaseModel): email:str=Field(min_length=3,max_length=254)
class Reset(BaseModel): token:str; password:str=Field(min_length=12,max_length=128)
def fail(exc): return HTTPException(400,detail={"code":str(exc),"message":"Request could not be completed"})
@router.post('/signup')
def signup(data:Signup):
 try:return auth_service.signup(data.email,data.password,data.display_name,data.organization)
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
