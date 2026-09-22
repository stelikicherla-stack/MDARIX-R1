"""Shared authentication setup for legacy protected-route integration tests."""
import uuid
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from auth.service import _hash, auth_service
from auth.durable import persist_session
from backend.app.db.models.foundation import AuthUser, Tenant, TenantMembership
from backend.app.db.session import SessionLocal

LEGACY_PROTECTED = {
    'test_day6_reality_graph', 'test_day7_product360_temporal', 'test_day8_evidence',
    'test_day9_retrieval', 'test_day10_investigation_workspace', 'test_day11_ai_investigator',
    'test_day12_hypothesis_engine', 'test_day15_decision_center', 'test_day17_briefs',
    'test_day18_trust_assurance',
}

def authenticated_client(application=app):
    client = TestClient(application)
    db = SessionLocal()
    tenant = db.query(Tenant).filter(Tenant.tenant_key == 'ACME_CARE_SYNTHETIC').first() or db.query(Tenant).first()
    user = db.query(AuthUser).filter(AuthUser.tenant_id == tenant.id, AuthUser.username == 'legacy-test-auth@synthetic.invalid').first()
    token = auth_service.signin_persisted('legacy-test-auth@synthetic.invalid', 'LegacyTestPassword123!', user_id=user.id, display_name=user.display_name, tenant_id=user.tenant_id, password_hash=user.password_hash, role=user.role, status=user.status, email_verified=user.email_verified)
    persist_session(db, token, user.id, user.tenant_id)
    db.close(); client.cookies.set('mdarix_session', token); return client

@pytest.fixture(autouse=True)
def authenticate_legacy_module(request):
    if request.module.__name__.split('.')[-1] not in LEGACY_PROTECTED:
        yield; return
    db = SessionLocal()
    try:
        tenant = db.query(Tenant).filter(Tenant.tenant_key == 'ACME_CARE_SYNTHETIC').first() or db.query(Tenant).first()
        email = 'legacy-test-auth@synthetic.invalid'
        user = db.query(AuthUser).filter(AuthUser.tenant_id == tenant.id, AuthUser.username == email).first()
        now = datetime.now(timezone.utc)
        if user is None:
            user = AuthUser(id=uuid.uuid4(), tenant_id=tenant.id, username=email, display_name='Legacy Test Auth', company='Test', password_hash=_hash('LegacyTestPassword123!'), role='Administrator', status='ACTIVE', email_verified=True, created_at=now, updated_at=now)
            db.add(user); db.flush()
        membership = db.query(TenantMembership).filter(TenantMembership.tenant_id == tenant.id, TenantMembership.user_id == user.id).first()
        if membership is None:
            db.add(TenantMembership(id=uuid.uuid4(), tenant_id=tenant.id, user_id=user.id, status='ACTIVE', is_default=True, created_at=now, updated_at=now))
        db.commit()
        token = auth_service.signin_persisted(email, 'LegacyTestPassword123!', user_id=user.id, display_name=user.display_name, tenant_id=user.tenant_id, password_hash=user.password_hash, role=user.role, status=user.status, email_verified=user.email_verified)
        persist_session(db, token, user.id, user.tenant_id)
        for value in vars(request.module).values():
            if not isinstance(value, type) and hasattr(value, 'cookies') and hasattr(value, 'get'):
                value.cookies.set('mdarix_session', token)
        yield
    finally:
        db.close()
