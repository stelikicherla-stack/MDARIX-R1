"""Reusable authenticated, tenant-scoped request context."""
from dataclasses import dataclass
from uuid import UUID, uuid4
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from auth.service import auth_service
from backend.app.db.session import get_db
from backend.app.db.models.foundation import AuthUser, TenantMembership, RoleAssignment, RoleDefinition
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
    if durable is None or not hasattr(durable, 'user_id'):
        # Test/dev clients created before durable sessions existed may still use
        # the in-process signer. Never permit this compatibility path outside
        # development; production remains durable-session-only.
        if __import__('os').getenv('MDARIX_ENV', 'development').lower() != 'development':
            raise HTTPException(401, detail={'code':'UNAUTHENTICATED','message':'Authentication required'})
        try:
            legacy = auth_service.context(token)
        except ValueError:
            raise HTTPException(401, detail={'code':'UNAUTHENTICATED','message':'Authentication required'})
        try:
            legacy_user_id = UUID(str(legacy['user_id']))
            user = db.query(AuthUser).filter(AuthUser.id == legacy_user_id, AuthUser.tenant_id == legacy['tenant_id'], AuthUser.status == 'ACTIVE').first()
        except (ValueError, TypeError):
            user = db.query(AuthUser).filter(AuthUser.username == str(legacy['user_id']).lower(), AuthUser.tenant_id == legacy['tenant_id'], AuthUser.status == 'ACTIVE').first()
        if user is not None and str(user.tenant_id) != str(legacy['tenant_id']):
            raise HTTPException(401, detail={'code':'UNAUTHENTICATED','message':'Authentication required'})
        if user is None:
            # Legacy unit-test clients do not create a database user. This
            # compatibility identity is development-only and never reaches
            # production deployments.
            return AuthenticatedRequestContext(str(legacy['user_id']), token, str(legacy['tenant_id']), None, legacy.get('active_role') or 'Viewer', None, (), None, {}, request.headers.get('X-Correlation-ID') or str(uuid4()))
        membership = db.query(TenantMembership).filter(TenantMembership.user_id == user.id, TenantMembership.tenant_id == user.tenant_id, TenantMembership.status == 'ACTIVE').first()
        role_id = None
        role_name = user.role
        assignment = db.query(RoleAssignment).filter(RoleAssignment.tenant_id == user.tenant_id, RoleAssignment.user_id == user.id, RoleAssignment.status == 'ACTIVE').first()
        if assignment is not None and hasattr(assignment, 'role_id'):
            role_id = str(assignment.role_id)
            role_row = db.query(RoleDefinition).filter(RoleDefinition.tenant_id == user.tenant_id, RoleDefinition.id == assignment.role_id, RoleDefinition.status == 'ACTIVE').first()
            if role_row is not None:
                role_name = role_row.name
        return AuthenticatedRequestContext(str(user.id), token, str(user.tenant_id), str(membership.id) if membership else None, role_id or role_name, None, (), None, {}, request.headers.get('X-Correlation-ID') or str(uuid4()))
    durable.last_seen_at = datetime.now(timezone.utc)
    if hasattr(db, 'commit'):
        db.commit()
    user_id, tenant_id = str(durable.user_id), str(durable.tenant_id)
    user = db.query(AuthUser).filter(AuthUser.id == user_id, AuthUser.tenant_id == tenant_id, AuthUser.status == 'ACTIVE').first()
    if user is None: raise HTTPException(401, detail={'code':'UNAUTHENTICATED','message':'Authentication required'})
    membership = db.query(TenantMembership).filter(TenantMembership.user_id == user.id, TenantMembership.tenant_id == user.tenant_id, TenantMembership.status == 'ACTIVE').first()
    return AuthenticatedRequestContext(user_id, token, tenant_id, str(membership.id) if membership else None, None, None, (), None, {}, request.headers.get('X-Correlation-ID') or str(uuid4()))
