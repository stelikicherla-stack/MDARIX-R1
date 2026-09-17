"""Focused Day 23 security checks that do not require a browser or secrets."""
import hashlib
import json

import pytest
import uuid
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from auth.service import LocalAuthService, auth_service
from backend.app.main import app
from backend.app.db.session import SessionLocal
from backend.app.db.models.foundation import ApprovalAuthority, AuditEvent, Decision, FeatureEntitlement, Investigation, SignedApprovalRecord, Tenant


def account():
    service = LocalAuthService()
    created = service.signup("day23@example.com", "Correct current password 123", "Day23 User", "Synthetic Co")
    return service, created


def test_user_id_is_server_account_identity_and_hash_is_not_password():
    service, created = account()
    assert created["user_id"] == "day23@example.com"
    assert "Correct current password 123" not in service.accounts["day23@example.com"].password_hash


def test_wrong_reauthentication_does_not_sign_or_change_account():
    service, created = account()
    service.verify_email(created["development_token"])
    session = service.signin("day23@example.com", "Correct current password 123")
    with pytest.raises(ValueError, match="INVALID_REAUTHENTICATION"):
        service.verify_current_password(session, "wrong password")
    assert service.context(session)["user_id"] == "day23@example.com"


def test_expired_or_unknown_session_cannot_reauthenticate():
    service, _ = account()
    with pytest.raises(ValueError, match="UNAUTHENTICATED"):
        service.verify_current_password("not-a-session", "Correct current password 123")


def test_signed_content_fingerprint_changes_on_material_change():
    original = {"object_id": "decision-1", "object_version": "v3", "decision": "APPROVE", "remarks": "Reviewed"}
    changed = {**original, "object_version": "v4"}
    first = hashlib.sha256(json.dumps(original, sort_keys=True).encode()).hexdigest()
    second = hashlib.sha256(json.dumps(changed, sort_keys=True).encode()).hexdigest()
    assert first != second


def test_replay_token_cannot_be_reused():
    service, created = account()
    service.verify_email(created["development_token"])
    with pytest.raises(ValueError, match="INVALID_VERIFICATION_TOKEN"):
        service.verify_email(created["development_token"])


def test_password_is_not_in_context_or_reset_response():
    service, created = account()
    service.verify_email(created["development_token"])
    assert "password" not in str(service.context(service.signin("day23@example.com", "Correct current password 123"))).lower()
    reset = service.request_reset("day23@example.com")
    assert "Correct current password 123" not in str(reset)


def _client(email, tenant_id):
    created=auth_service.signup(email,"Correct current password 123",email.split("@")[0],"Day23")
    auth_service.accounts[email].tenant_id=str(tenant_id)
    auth_service.verify_email(created["development_token"])
    token=auth_service.signin(email,"Correct current password 123")
    client=TestClient(app); client.cookies.set("mdarix_session",token); return client


def _decision(db, tenant_id, investigation, creator):
    now=datetime.now(timezone.utc); row=Decision(id=uuid.uuid4(),tenant_id=tenant_id,investigation_id=investigation.id,decision_identifier=f"D23-{uuid.uuid4().hex[:10]}",decision_type="INVESTIGATION_REVIEW",disposition="REQUIRES_REVIEW",rationale="Day23 API matrix",decision_status="REQUIRES_REVIEW",authorized_by_ref=creator,updated_at=now,decision_timestamp=now,created_at=now)
    db.add(row); db.commit(); return row


def test_api_signing_security_matrix():
    db=SessionLocal(); tenant=db.query(Tenant).filter(Tenant.status=="active").first(); investigation=db.query(Investigation).filter_by(tenant_id=tenant.id).first(); ids=[]
    approver=f"approver-{uuid.uuid4().hex[:8]}@example.com"; creator=f"creator-{uuid.uuid4().hex[:8]}@example.com"; approver_client=_client(approver,tenant.id); creator_client=_client(creator,tenant.id)
    try:
        assert approver_client.get("/api/v1/governance/effective-access").status_code==200
        first=_decision(db,tenant.id,investigation,creator); ids.append(first.id); version=first.updated_at.isoformat()
        wrong=approver_client.post(f"/api/v1/governance/decisions/{first.id}/sign",json={"decision":"APPROVE","remarks":"Reviewed","password":"wrong password","object_version":version}); assert wrong.status_code==403
        db.expire_all(); assert db.query(SignedApprovalRecord).filter_by(object_id=first.id).count()==0
        signed=approver_client.post(f"/api/v1/governance/decisions/{first.id}/sign",json={"decision":"APPROVE","remarks":"Reviewed","password":"Correct current password 123","object_version":version}); assert signed.status_code==200
        replay=approver_client.post(f"/api/v1/governance/decisions/{first.id}/sign",json={"decision":"APPROVE","remarks":"Reviewed","password":"Correct current password 123","object_version":version}); assert replay.status_code==409
        db.expire_all(); assert db.query(SignedApprovalRecord).filter_by(object_id=first.id).count()==1
        own=_decision(db,tenant.id,investigation,creator); ids.append(own.id); own_result=creator_client.post(f"/api/v1/governance/decisions/{own.id}/sign",json={"decision":"APPROVE","remarks":"Self","password":"Correct current password 123","object_version":own.updated_at.isoformat()}); assert own_result.status_code==403 and own_result.json()["detail"]["code"]=="SOD_DENIED"
        stale=_decision(db,tenant.id,investigation,creator); ids.append(stale.id); stale_version=stale.updated_at.isoformat(); changed=approver_client.post(f"/api/v1/governance/decisions/{stale.id}/material-change",json={"change_summary":"Material conclusion updated","expected_updated_at":stale_version}); assert changed.status_code==200
        stale_sign=approver_client.post(f"/api/v1/governance/decisions/{stale.id}/sign",json={"decision":"REJECT","remarks":"Old version","password":"Correct current password 123","object_version":stale_version}); assert stale_sign.status_code==409
        db.expire_all(); assert db.query(SignedApprovalRecord).filter_by(object_id=stale.id).count()==0
        entitlement=db.query(FeatureEntitlement).filter_by(feature_code="DECISION_CENTER_SIGNATURES").first(); entitlement.enabled=False; db.commit(); denied=_decision(db,tenant.id,investigation,creator); ids.append(denied.id); assert approver_client.post(f"/api/v1/governance/decisions/{denied.id}/sign",json={"decision":"APPROVE","remarks":"Denied","password":"Correct current password 123","object_version":denied.updated_at.isoformat()}).status_code==403; entitlement.enabled=True; db.commit()
        authority=db.query(ApprovalAuthority).filter_by(tenant_id=tenant.id,role_name="Viewer").first(); authority.status="REVOKED"; db.commit(); no_authority=_decision(db,tenant.id,investigation,creator); ids.append(no_authority.id); assert approver_client.post(f"/api/v1/governance/decisions/{no_authority.id}/sign",json={"decision":"APPROVE","remarks":"Denied","password":"Correct current password 123","object_version":no_authority.updated_at.isoformat()}).status_code==403; authority.status="ACTIVE"; db.commit()
        other=Tenant(id=uuid.uuid4(),tenant_key=f"D23-{uuid.uuid4().hex[:8]}",name="Other synthetic tenant",status="active",created_at=datetime.now(timezone.utc),updated_at=datetime.now(timezone.utc)); db.add(other); db.commit(); foreign_client=_client(f"foreign-{uuid.uuid4().hex[:8]}@example.com",other.id); assert foreign_client.post(f"/api/v1/governance/decisions/{first.id}/sign",json={"decision":"REJECT","remarks":"Cross tenant","password":"Correct current password 123","object_version":version}).status_code in {403,404}; assert foreign_client.get(f"/api/v1/governance/decisions/{first.id}/signature-history").json()==[]
    finally:
        db.query(SignedApprovalRecord).filter(SignedApprovalRecord.object_id.in_(ids)).delete(synchronize_session=False); db.query(AuditEvent).filter(AuditEvent.entity_id.in_(ids)).delete(synchronize_session=False); db.query(Decision).filter(Decision.id.in_(ids)).delete(synchronize_session=False); db.commit(); db.close()
