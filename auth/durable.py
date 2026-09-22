"""Database-backed authentication sessions and one-time links."""
from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from sqlalchemy.orm import Session
from backend.app.db.models.stage2 import AuthSession, UserInvitation, PasswordResetRequest

def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()

def persist_session(db: Session, raw: str, user_id, tenant_id, ttl: int = 3600):
    if not hasattr(db, 'add'):
        return
    now = datetime.now(timezone.utc)
    db.add(AuthSession(session_hash=hash_token(raw), user_id=user_id, tenant_id=tenant_id,
                       expires_at=now + timedelta(seconds=ttl), created_at=now, last_seen_at=now))
    db.commit()

def revoke_session(db: Session, raw: str):
    row = db.query(AuthSession).filter(AuthSession.session_hash == hash_token(raw), AuthSession.revoked_at.is_(None)).first()
    if row:
        row.revoked_at = datetime.now(timezone.utc); db.commit()

def issue_invitation(db: Session, user_id, tenant_id, created_by=None, ttl: int = 3600):
    raw = secrets.token_urlsafe(32); now = datetime.now(timezone.utc)
    db.add(UserInvitation(user_id=user_id, tenant_id=tenant_id, token_hash=hash_token(raw), expires_at=now + timedelta(seconds=ttl), created_at=now, created_by=created_by)); db.commit(); return raw

def issue_reset(db: Session, user_id, tenant_id, created_by=None, ttl: int = 3600):
    raw = secrets.token_urlsafe(32); now = datetime.now(timezone.utc)
    db.add(PasswordResetRequest(user_id=user_id, tenant_id=tenant_id, token_hash=hash_token(raw), expires_at=now + timedelta(seconds=ttl), created_at=now, created_by=created_by)); db.commit(); return raw

def consume(db: Session, raw: str, kind: str):
    model = UserInvitation if kind == 'activation' else PasswordResetRequest
    row = db.query(model).filter(model.token_hash == hash_token(raw), model.used_at.is_(None), model.expires_at > datetime.now(timezone.utc)).first()
    if not row: raise ValueError(f'INVALID_{kind.upper()}_TOKEN')
    row.used_at = datetime.now(timezone.utc); db.commit(); return str(row.user_id)
