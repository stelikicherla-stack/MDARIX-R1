"""Create deterministic, synthetic Day 27 live Tenant A/B retrieval fixtures.

Run manually in the R1 development environment only. This is a CLI fixture
tool, not an application route and never runs during normal startup.
"""
from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Allow `python scripts/day27_live_fixture.py` from the repository root.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sqlalchemy.orm import Session

from auth.service import _hash
from backend.app.db.models.foundation import AuthUser, Evidence, Investigation, Product, ProductVersion, Tenant
from backend.app.db.session import SessionLocal
from backend.app.governance_router import bootstrap


PASSWORD = os.environ.get("DAY27_FIXTURE_PASSWORD", "")
if len(PASSWORD) < 12:
    raise SystemExit("Set DAY27_FIXTURE_PASSWORD to a synthetic password of at least 12 characters.")


def now():
    return datetime.now(timezone.utc)


def ensure_fixture(db: Session, suffix: str) -> dict[str, str]:
    timestamp = now()
    tenant_key = f"DAY27_{suffix}"
    tenant = db.query(Tenant).filter(Tenant.tenant_key == tenant_key).first()
    if tenant is None:
        tenant = Tenant(id=uuid.uuid4(), tenant_key=tenant_key, name=f"Day 27 Synthetic Tenant {suffix}", status="active", created_at=timestamp, updated_at=timestamp)
        db.add(tenant); db.flush()
    email = f"day27-{suffix.lower()}@synthetic.invalid"
    user = db.query(AuthUser).filter(AuthUser.tenant_id == tenant.id, AuthUser.username == email).first()
    if user is None:
        user = AuthUser(id=uuid.uuid4(), tenant_id=tenant.id, username=email, display_name=f"Day 27 User {suffix}", company=f"Day 27 Synthetic {suffix}", password_hash=_hash(PASSWORD), role="Viewer", status="ACTIVE", email_verified=True, created_at=timestamp, updated_at=timestamp)
        db.add(user); db.flush()
    else:
        # This account is a deterministic synthetic fixture identity. Refresh
        # only its password so reruns can safely rotate the temporary secret.
        user.password_hash = _hash(PASSWORD)
        user.updated_at = timestamp
    bootstrap(db, tenant)
    product_identifier = f"TENANT_{suffix}_PRODUCT_CANARY"
    product = db.query(Product).filter(Product.tenant_id == tenant.id, Product.product_identifier == product_identifier).first()
    if product is None:
        product = Product(id=uuid.uuid4(), tenant_id=tenant.id, product_identifier=product_identifier, name=f"Synthetic Product {suffix}", description=f"TENANT_{suffix}_PRODUCT_CANARY", lifecycle_status="active", product_family="DAY27", created_at=timestamp, updated_at=timestamp)
        db.add(product); db.flush()
    version_identifier = f"TENANT_{suffix}_VERSION_CANARY"
    version = db.query(ProductVersion).filter(ProductVersion.tenant_id == tenant.id, ProductVersion.product_id == product.id, ProductVersion.version_identifier == version_identifier).first()
    if version is None:
        version = ProductVersion(id=uuid.uuid4(), tenant_id=tenant.id, product_id=product.id, version_identifier=version_identifier, description=f"TENANT_{suffix}_VERSION_CANARY", lifecycle_status="active", created_at=timestamp, updated_at=timestamp)
        db.add(version); db.flush()
    investigation = db.query(Investigation).filter(Investigation.tenant_id == tenant.id, Investigation.investigation_identifier == f"DAY27-{suffix}").first()
    if investigation is None:
        investigation = Investigation(id=uuid.uuid4(), tenant_id=tenant.id, product_id=product.id, investigation_identifier=f"DAY27-{suffix}", investigation_question="Synthetic authorized retrieval isolation validation", status="open", opened_at=timestamp, created_at=timestamp, updated_at=timestamp)
        db.add(investigation); db.flush()
    evidence_identifier = f"TENANT_{suffix}_EVIDENCE_CANARY"
    evidence = db.query(Evidence).filter(Evidence.tenant_id == tenant.id, Evidence.evidence_identifier == evidence_identifier).first()
    if evidence is None:
        evidence = Evidence(id=uuid.uuid4(), tenant_id=tenant.id, investigation_id=investigation.id, evidence_identifier=evidence_identifier, evidence_type="DAY27_SYNTHETIC", title=f"Synthetic Evidence {suffix}", source_reference=f"DAY27-{suffix}", reliability_status="reviewed", fact_type="source_fact", content=f"TENANT_{suffix}_EVIDENCE_CANARY", created_at=timestamp, updated_at=timestamp)
        db.add(evidence)
    db.commit()
    return {"tenant_key": tenant_key, "tenant_id": str(tenant.id), "email": email, "product_id": str(product.id), "version_id": str(version.id), "evidence_id": str(evidence.id)}


if __name__ == "__main__":
    with SessionLocal() as db:
        print(ensure_fixture(db, "A"))
        print(ensure_fixture(db, "B"))
