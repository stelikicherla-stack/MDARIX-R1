import uuid

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.models.foundation import AuthUser, Tenant
from backend.app.db.models.stage2 import OnboardingRequest
from backend.app.db.session import SessionLocal


def test_public_signup_creates_pending_request_not_tenant():
    email = f"onboarding-{uuid.uuid4().hex[:10]}@example.invalid"
    db = SessionLocal()
    before = db.query(Tenant).count()
    db.close()
    try:
        response = TestClient(app).post(
            "/api/v1/auth/signup",
            json={
                "email": email,
                "password": "TemporaryPassword123!",
                "display_name": "Pending Customer",
                "organization": "Pending Organization",
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ONBOARDING_REQUEST_ACCEPTED"
        assert body["tenant_created"] is False

        db = SessionLocal()
        assert db.query(Tenant).count() == before
        assert db.query(AuthUser).filter(AuthUser.username == email).first() is None
        assert db.query(OnboardingRequest).filter(OnboardingRequest.email == email).count() == 1
    finally:
        db.query(OnboardingRequest).filter(OnboardingRequest.email == email).delete()
        db.commit()
        db.close()
