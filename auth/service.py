from __future__ import annotations
import hashlib, hmac, secrets, time
from dataclasses import dataclass
from email.utils import parseaddr

def _hash(password, salt=None):
    salt=salt or secrets.token_bytes(16); return salt.hex()+":"+hashlib.scrypt(password.encode(),salt=salt,n=2**14,r=8,p=1).hex()
def _verify(password, stored):
    salt, digest=stored.split(":",1); return hmac.compare_digest(_hash(password,bytes.fromhex(salt)).split(":",1)[1],digest)
@dataclass
class Account:
    user_id:str; email:str; display_name:str; tenant_id:str; password_hash:str; status:str="PENDING_VERIFICATION"; role:str="Viewer"; verified:bool=False

class LocalAuthService:
    def __init__(self): self.accounts={}; self.tokens={}; self.sessions={}; self.failed={}
    def signup(self, email, password, display_name, organization):
        email=email.strip().lower();
        if "@" not in parseaddr(email)[1] or len(email)>254: raise ValueError("VALID_EMAIL_REQUIRED")
        if len(password)<12 or len(password)>128: raise ValueError("PASSWORD_POLICY")
        if email in self.accounts: raise ValueError("ACCOUNT_EXISTS")
        account=Account(secrets.token_hex(16),email,display_name[:120],"sandbox-"+secrets.token_hex(6),_hash(password)); self.accounts[email]=account; token=self._token(account.user_id,"verify"); return {"user_id":account.user_id,"status":account.status,"verification_required":True,"development_token":token}
    def _token(self, user_id, kind):
        raw=secrets.token_urlsafe(32); self.tokens[hashlib.sha256(raw.encode()).hexdigest()]={"user_id":user_id,"kind":kind,"expires":time.time()+3600,"used":False}; return raw
    def verify_email(self, raw):
        item=self.tokens.get(hashlib.sha256(raw.encode()).hexdigest());
        if not item or item["kind"]!="verify" or item["used"] or item["expires"]<time.time(): raise ValueError("INVALID_VERIFICATION_TOKEN")
        account=next(a for a in self.accounts.values() if a.user_id==item["user_id"]); item["used"]=True; account.verified=True; account.status="ACTIVE"; return {"status":"ACTIVE","user_id":account.user_id}
    def signin(self,email,password):
        identifier=email.strip().lower(); account=self.accounts.get(identifier) or next((item for item in self.accounts.values() if item.user_id.lower()==identifier),None)
        if not account or not _verify(password,account.password_hash) or account.status!="ACTIVE": raise ValueError("INVALID_CREDENTIALS")
        session=secrets.token_urlsafe(32); self.sessions[hashlib.sha256(session.encode()).hexdigest()]={"user_id":account.user_id,"expires":time.time()+3600}; return session
    def context(self, session):
        item=self.sessions.get(hashlib.sha256(session.encode()).hexdigest());
        if not item or item["expires"]<time.time(): raise ValueError("UNAUTHENTICATED")
        account=next(a for a in self.accounts.values() if a.user_id==item["user_id"]); return {"user_id":account.user_id,"display_name":account.display_name,"email":account.email,"tenant_id":account.tenant_id,"active_role":account.role}
    def signout(self,session): self.sessions.pop(hashlib.sha256(session.encode()).hexdigest(),None)
    def request_reset(self,email):
        account=self.accounts.get(email.strip().lower()); return {"status":"RESET_REQUEST_ACCEPTED","development_token":self._token(account.user_id,"reset") if account else None}
    def reset(self,raw,password):
        item=self.tokens.get(hashlib.sha256(raw.encode()).hexdigest());
        if not item or item["kind"]!="reset" or item["used"] or item["expires"]<time.time() or len(password)<12: raise ValueError("INVALID_RESET")
        account=next(a for a in self.accounts.values() if a.user_id==item["user_id"]); account.password_hash=_hash(password); item["used"]=True; return {"status":"PASSWORD_RESET"}
auth_service=LocalAuthService()
