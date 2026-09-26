"""Explicitly gated provisioning of the deterministic Day 35 identity fixture."""
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from access_control.fixtures import FIXTURE_TENANTS, FIXTURE_USERS, validate_fixture
from auth.service import _hash
from backend.app.db.models.customer_lifecycle import Customer
from backend.app.db.models.foundation import AuthUser, PersonaAssignment, Tenant, TenantMembership
from backend.app.db.session import SessionLocal


def main() -> int:
    validate_fixture()
    if os.getenv("DAY35_FIXTURE_APPLY") != "1":
        print("DAY35_FIXTURE_APPLY = DISABLED")
        print("Set DAY35_FIXTURE_APPLY=1 to permit local synthetic database writes.")
        return 2
    password = os.getenv("DAY35_FIXTURE_PASSWORD")
    if not password or len(password) < 12:
        print("DAY35_FIXTURE_PASSWORD must be a synthetic password of at least 12 characters.")
        return 2
    reset_existing = os.getenv("DAY35_FIXTURE_RESET_PASSWORD") == "1"

    now = datetime.now(timezone.utc)
    db = SessionLocal()
    try:
        tenants = {}
        for fixture in FIXTURE_TENANTS:
            tenant = db.query(Tenant).filter(Tenant.tenant_key == fixture.key).first()
            if tenant is None:
                customer = Customer(
                    id=uuid.uuid4(),
                    customer_identifier=f"CUST-{fixture.key.removeprefix('R1_TENANT_')}",
                    legal_name=fixture.name,
                    display_name=fixture.name,
                    customer_type="SYNTHETIC",
                    country="UNSPECIFIED",
                    lifecycle_status="ACTIVE",
                    lock_version=1,
                    created_at=now,
                    updated_at=now,
                )
                db.add(customer)
                db.flush()
                tenant = Tenant(id=uuid.uuid4(), customer_id=customer.id, tenant_key=fixture.key,
                                tenant_identifier=fixture.key, tenant_slug=fixture.key.lower(),
                                display_name=fixture.name, name=fixture.name, tenant_type="STANDARD",
                                deployment_model="SHARED", primary_region="UNSPECIFIED",
                                residency_region="UNSPECIFIED", cross_border_processing_allowed=False,
                                provisioning_status="PROVISIONED", status="ACTIVE", lock_version=1,
                                activated_at=now, created_at=now, updated_at=now)
                db.add(tenant); db.flush()
            tenants[fixture.key] = tenant
        for fixture in FIXTURE_USERS:
            tenant = tenants[fixture.tenant_key]
            user = db.query(AuthUser).filter(AuthUser.tenant_id == tenant.id, AuthUser.username == fixture.email).first()
            if user is None:
                user = AuthUser(id=uuid.uuid4(), tenant_id=tenant.id, username=fixture.email, display_name=fixture.key, company=tenant.name, password_hash=_hash(password), role=fixture.role, status="ACTIVE", email_verified=True, created_at=now, updated_at=now)
                db.add(user); db.flush()
            elif reset_existing:
                user.password_hash = _hash(password)
                user.status = "ACTIVE"
                user.email_verified = True
                user.updated_at = now
            membership = db.query(TenantMembership).filter_by(tenant_id=tenant.id, user_id=user.id).first()
            if membership is None:
                db.add(TenantMembership(id=uuid.uuid4(), tenant_id=tenant.id, user_id=user.id, status="ACTIVE", is_default=True, created_at=now, updated_at=now))
            for persona in fixture.personas:
                assignment = db.query(PersonaAssignment).filter_by(tenant_id=tenant.id, user_id=user.id, persona_code=persona).first()
                if assignment is None:
                    db.add(PersonaAssignment(id=uuid.uuid4(), tenant_id=tenant.id, user_id=user.id, persona_code=persona, status="ACTIVE", created_at=now, updated_at=now))
        db.commit()
        print(f"DAY35_FIXTURE_APPLY = PASS ({len(tenants)} tenants, {len(FIXTURE_USERS)} users)")
        print(f"DAY35_FIXTURE_PASSWORD_RESET = {'PASS' if reset_existing else 'NOT_REQUESTED'}")
        return 0
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
