import os, hashlib, secrets
from fastapi import APIRouter, HTTPException, Response, Request, Depends
from pydantic import BaseModel, Field
from auth.service import auth_service, _hash
from auth.emailer import send_password_reset_email, send_verification_email
from backend.app.db.session import get_db
from backend.app.db.models.foundation import AuthUser, TenantMembership
from backend.app.db.models.stage2 import OnboardingRequest
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from auth.durable import persist_session, revoke_session, issue_reset, consume
from auth.durable import hash_token
from backend.app.db.models.stage2 import AuthSession, LoginThrottle, PasswordHistory, MfaChallenge
from datetime import timedelta
router=APIRouter(prefix="/api/v1/auth",tags=["Authentication"])
class Signup(BaseModel): email:str=Field(min_length=3,max_length=254); password: str=Field(min_length=12,max_length=128); display_name:str=Field(min_length=1,max_length=120); organization:str=Field(min_length=1,max_length=160)
class Signin(BaseModel): email:str; password:str
class Verify(BaseModel): token:str
class ResetRequest(BaseModel): email:str=Field(min_length=3,max_length=254)
class Reset(BaseModel): token:str; password:str=Field(min_length=12,max_length=128)
class MfaCode(BaseModel): code: str = Field(min_length=6, max_length=6)
def fail(exc): return HTTPException(400,detail={"code":str(exc),"message":"Request could not be completed"})
def _development_token(token: str | None) -> str | None:
    return token if os.getenv("MDARIX_ENV", "development").lower() == "development" else None
def _legacy_compat_enabled() -> bool:
    """Allow in-process compatibility only for explicitly enabled local tests."""
    return (
        os.getenv("MDARIX_ENV", "development").lower() == "development"
        and os.getenv("MDARIX_ALLOW_LEGACY_AUTH_FALLBACK", "").lower() == "true"
    )
def _password_reuse(db, row, new_password: str) -> bool:
    """Return true when the proposed password matches the current or last five passwords."""
    from auth.service import _verify
    if _verify(new_password, row.password_hash):
        return True
    history = db.query(PasswordHistory).filter_by(tenant_id=row.tenant_id, user_id=row.id).order_by(PasswordHistory.created_at.desc()).limit(5).all()
    return any(_verify(new_password, item.password_hash) for item in history)

def _record_password_change(db, row, password_hash: str, now: datetime) -> None:
    db.add(PasswordHistory(id=__import__('uuid').uuid4(), tenant_id=row.tenant_id, user_id=row.id, password_hash=password_hash, created_at=now))
    row.password_changed_at = now
    row.password_expires_at = now + timedelta(days=int(os.getenv("MDARIX_PASSWORD_MAX_AGE_DAYS", "90")))

def _mfa_hash(code: str) -> str:
    return hashlib.sha256(code.encode("ascii")).hexdigest()

@router.post('/mfa/enroll')
def mfa_enroll(request: Request, db: Session = Depends(get_db)):
    """Begin a durable MFA enrollment; the one-time code is never persisted."""
    token = request.cookies.get('mdarix_session', '')
    row = db.query(AuthSession).filter(AuthSession.session_hash == hash_token(token), AuthSession.revoked_at.is_(None)).first()
    if not row: raise HTTPException(401, detail={"code":"UNAUTHENTICATED","message":"Authentication required"})
    user = db.query(AuthUser).filter(AuthUser.id == row.user_id, AuthUser.tenant_id == row.tenant_id).first()
    if not user: raise HTTPException(401, detail={"code":"UNAUTHENTICATED","message":"Authentication required"})
    code = f"{secrets.randbelow(1000000):06d}"; now = datetime.now(timezone.utc)
    db.query(MfaChallenge).filter(MfaChallenge.user_id == user.id, MfaChallenge.tenant_id == user.tenant_id, MfaChallenge.used_at.is_(None)).update({"used_at": now})
    db.add(MfaChallenge(id=__import__('uuid').uuid4(), user_id=user.id, tenant_id=user.tenant_id, code_hash=_mfa_hash(code), purpose="ENROLLMENT", expires_at=now + timedelta(minutes=10), created_at=now))
    db.commit()
    return {"status":"MFA_ENROLLMENT_PENDING", "expires_at": now + timedelta(minutes=10), "development_code": code if os.getenv("MDARIX_ENV", "development").lower() == "development" else None}

@router.post('/mfa/verify-enrollment')
def mfa_verify_enrollment(data: MfaCode, request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get('mdarix_session', '')
    challenge = db.query(MfaChallenge).join(AuthSession, AuthSession.user_id == MfaChallenge.user_id).filter(AuthSession.session_hash == hash_token(token), MfaChallenge.purpose == "ENROLLMENT", MfaChallenge.used_at.is_(None), MfaChallenge.expires_at > datetime.now(timezone.utc)).order_by(MfaChallenge.created_at.desc()).first()
    if not challenge or challenge.attempts >= 5: raise HTTPException(400, detail={"code":"MFA_CHALLENGE_INVALID","message":"MFA challenge is invalid or expired"})
    challenge.attempts += 1
    if not secrets.compare_digest(challenge.code_hash, _mfa_hash(data.code)):
        db.commit(); raise HTTPException(403, detail={"code":"MFA_CODE_INVALID","message":"MFA code is invalid"})
    now = datetime.now(timezone.utc); challenge.used_at = now
    user = db.query(AuthUser).filter(AuthUser.id == challenge.user_id, AuthUser.tenant_id == challenge.tenant_id).first(); user.mfa_required = True; user.mfa_enrolled_at = now
    db.commit(); return {"status":"MFA_ENROLLED", "user_id": str(user.id), "enrolled_at": now}

@router.post('/mfa/challenge')
def mfa_challenge(request: Request, db: Session = Depends(get_db)):
    """Issue a durable, single-use challenge for a governed signature."""
    token = request.cookies.get('mdarix_session', '')
    session = db.query(AuthSession).filter(AuthSession.session_hash == hash_token(token), AuthSession.revoked_at.is_(None), AuthSession.expires_at > datetime.now(timezone.utc)).first()
    if not session: raise HTTPException(401, detail={"code":"UNAUTHENTICATED","message":"Authentication required"})
    user = db.query(AuthUser).filter(AuthUser.id == session.user_id, AuthUser.tenant_id == session.tenant_id, AuthUser.status == "ACTIVE").first()
    if not user or not user.mfa_required or not user.mfa_enrolled_at: raise HTTPException(403, detail={"code":"MFA_NOT_ENROLLED","message":"Enroll MFA before requesting a signature challenge"})
    code = f"{secrets.randbelow(1000000):06d}"; now = datetime.now(timezone.utc)
    db.query(MfaChallenge).filter(MfaChallenge.user_id == user.id, MfaChallenge.tenant_id == user.tenant_id, MfaChallenge.purpose == "SIGNATURE", MfaChallenge.used_at.is_(None)).update({"used_at": now})
    db.add(MfaChallenge(id=__import__('uuid').uuid4(), user_id=user.id, tenant_id=user.tenant_id, code_hash=_mfa_hash(code), purpose="SIGNATURE", expires_at=now + timedelta(minutes=5), created_at=now)); db.commit()
    return {"status":"MFA_CHALLENGE_ISSUED", "expires_at": now + timedelta(minutes=5), "development_code": code if os.getenv("MDARIX_ENV", "development").lower() == "development" else None}
@router.post('/signup')
def signup(data:Signup, db:Session=Depends(get_db)):
 try:
  email = data.email.strip().lower()
  if db.query(AuthUser).filter(AuthUser.username == email).first():
   raise ValueError("ACCOUNT_EXISTS")
  existing = db.query(OnboardingRequest).filter(OnboardingRequest.email == email).first()
  if existing:
   return {"status": "ONBOARDING_REQUEST_ACCEPTED", "request_id": str(existing.id), "request_status": existing.status}
  now = datetime.now(timezone.utc)
  request = OnboardingRequest(id=__import__('uuid').uuid4(), email=email, display_name=data.display_name.strip(), organization=data.organization.strip(), status="PENDING_REVIEW", created_at=now, updated_at=now)
  db.add(request); db.commit()
  return {"status": "ONBOARDING_REQUEST_ACCEPTED", "request_id": str(request.id), "request_status": request.status, "tenant_created": False, "next_step": "A Platform Administrator must provision the tenant and invite the initial Customer Administrator."}
 except ValueError as e: raise fail(e)
 except Exception as e: db.rollback(); raise HTTPException(400,detail={"code":"ONBOARDING_REQUEST_FAILED","message":"The onboarding request could not be recorded."}) from e
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
  identifier=data.email.strip().lower(); now=datetime.now(timezone.utc)
  throttle_query=db.query(LoginThrottle).filter(LoginThrottle.identifier==identifier)
  throttle=throttle_query.with_for_update().first() if hasattr(throttle_query, 'with_for_update') else throttle_query.first()
  if throttle is not None and not hasattr(throttle, 'failure_count'):
   throttle = None
  if throttle and throttle.locked_until and throttle.locked_until > now:
   raise HTTPException(429,detail={"code":"ACCOUNT_TEMPORARILY_LOCKED","message":"Too many failed sign-in attempts. Try again later."})
  row=db.query(AuthUser).filter(AuthUser.username==identifier).first()
  if not row: raise ValueError("INVALID_CREDENTIALS")
  if row.password_expires_at and row.password_expires_at <= now:
   raise HTTPException(403,detail={"code":"PASSWORD_EXPIRED","message":"Password change is required before sign-in."})
  token=auth_service.signin_persisted(data.email,data.password,user_id=row.id,display_name=row.display_name,tenant_id=row.tenant_id,password_hash=row.password_hash,role=row.role,status=row.status,email_verified=row.email_verified)
  if throttle:
   throttle.failure_count=0; throttle.locked_until=None; throttle.last_failure_at=None; throttle.updated_at=now
  if hasattr(db, 'commit'):
   db.commit()
  persist_session(db, token, row.id, row.tenant_id)
  is_development = os.getenv('MDARIX_ENV','development').lower() == 'development'
  secure_cookie = True if not is_development else os.getenv('MDARIX_COOKIE_SECURE','false').lower() == 'true'
  response.set_cookie('mdarix_session',token,httponly=True,samesite='lax',secure=secure_cookie,max_age=3600); return auth_service.context(token)
 except ValueError as e:
  identifier=data.email.strip().lower(); now=datetime.now(timezone.utc)
  throttle_query=db.query(LoginThrottle).filter(LoginThrottle.identifier==identifier)
  throttle=throttle_query.with_for_update().first() if hasattr(throttle_query, 'with_for_update') else throttle_query.first()
  if throttle is not None and not hasattr(throttle, 'failure_count'):
   throttle = None
  if throttle is None:
   throttle=LoginThrottle(identifier=identifier,failure_count=0,updated_at=now); db.add(throttle)
  throttle.failure_count += 1; throttle.last_failure_at=now; throttle.updated_at=now
  if throttle.failure_count >= 5:
   from datetime import timedelta
   throttle.locked_until=now+timedelta(minutes=15)
  db.commit()
  raise HTTPException(401,detail={"code":"INVALID_CREDENTIALS","message":"Invalid credentials."}) from e
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
  now=datetime.now(timezone.utc)
  if _password_reuse(db, row, data.password): raise ValueError("PASSWORD_REUSE_NOT_ALLOWED")
  row.password_hash=_hash(data.password); row.status="ACTIVE"; row.email_verified=True; row.updated_at=now; _record_password_change(db,row,row.password_hash,now)
  db.query(TenantMembership).filter(TenantMembership.tenant_id==row.tenant_id,TenantMembership.user_id==row.id).update({"status":"ACTIVE","updated_at":datetime.now(timezone.utc)})
  db.commit()
  return {"status":"PASSWORD_RESET"}
 except ValueError:
  if not _legacy_compat_enabled():
   raise fail("INVALID_RESET")
  try:return auth_service.reset(data.token,data.password)
  except ValueError as e: raise fail(e)

@router.post('/activate-account')
def activate(data:Reset, db:Session=Depends(get_db)):
 try:
  user_id=consume(db, data.token, "activation")
  row=db.query(AuthUser).filter(AuthUser.id==user_id).first()
  if row is None: raise ValueError("INVALID_ACTIVATION")
  now=datetime.now(timezone.utc)
  if _password_reuse(db, row, data.password): raise ValueError("PASSWORD_REUSE_NOT_ALLOWED")
  row.password_hash=_hash(data.password); row.status="ACTIVE"; row.email_verified=True; row.updated_at=now; _record_password_change(db,row,row.password_hash,now); db.commit()
  db.query(TenantMembership).filter(TenantMembership.tenant_id==row.tenant_id,TenantMembership.user_id==row.id).update({"status":"ACTIVE","updated_at":datetime.now(timezone.utc)})
  db.commit()
  return {"status":"ACTIVE","user_id":str(row.id),"email":row.username}
 except ValueError as e: raise fail(e)
