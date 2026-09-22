"""Reusable authenticated, tenant-scoped request context."""
from dataclasses import dataclass
from uuid import uuid4
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from auth.service import auth_service
from backend.app.db.session import get_db
from backend.app.db.models.foundation import AuthUser, TenantMembership
from backend.app.db.models.stage2 import AuthSession
from auth.durable import hash_token
from datetime import datetime, timezone

@dataclass(frozen=True)
class AuthenticatedRequestContext:
    user_id: str; session_id: str; tenant_id: str; membership_id: str | None; active_role_id: str | None; persona: str | None; permission_set_ids: tuple[str, ...]; plan_id: str | None; entitlements: dict; correlation_id: str

def get_request_context(request: Request, db: Session = Depends(get_db)) -> AuthenticatedRequestContext:
    token = request.cookies.get('mdarix_session')
    if not token: raise HTTPException(401, detail={'code':'UNAUTHENTICATED','message':'Authentication required'})
    durable = db.query(AuthSession).filter(AuthSession.session_hash == hash_token(token), AuthSession.revoked_at.is_(None), AuthSession.expires_at > datetime.now(timezone.utc)).first()
    if durable is None:
        raise HTTPException(401, detail={'code':'UNAUTHENTICATED','message':'Authentication required'})
    durable.last_seen_at = datetime.now(timezone.utc)
    db.commit()
    user_id, tenant_id = str(durable.user_id), str(durable.tenant_id)
    user = db.query(AuthUser).filter(AuthUser.id == user_id, AuthUser.tenant_id == tenant_id, AuthUser.status == 'ACTIVE').first()
    if user is None: raise HTTPException(401, detail={'code':'UNAUTHENTICATED','message':'Authentication required'})
    membership = db.query(TenantMembership).filter(TenantMembership.user_id == user.id, TenantMembership.tenant_id == user.tenant_id, TenantMembership.status == 'ACTIVE').first()
    return AuthenticatedRequestContext(user_id, token, tenant_id, str(membership.id) if membership else None, None, None, (), None, {}, request.headers.get('X-Correlation-ID') or str(uuid4()))
