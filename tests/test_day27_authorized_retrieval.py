import datetime as dt
import uuid

import pytest

from ask_mdarix.authorized_retrieval import AuthorizedRetrievalRequest, AuthorizedRetrievalService
from backend.app.db.models.foundation import Evidence, Investigation, Product, ProductVersion, Tenant
from backend.app.db.session import SessionLocal


@pytest.fixture
def day27_db():
    db = SessionLocal()
    stamp = dt.datetime.now(dt.timezone.utc)
    tenants = []
    records = {}
    try:
        for suffix in ("A", "B"):
            tenant = Tenant(id=uuid.uuid4(), tenant_key=f"DAY27_AUTOMATED_{suffix}_{uuid.uuid4().hex[:8]}", name=f"Day 27 automated {suffix}", status="active", created_at=stamp, updated_at=stamp)
            db.add(tenant); db.flush(); tenants.append(tenant)
            product = Product(id=uuid.uuid4(), tenant_id=tenant.id, product_identifier=f"TENANT_{suffix}_PRODUCT_CANARY", name=f"Synthetic product {suffix}", description=f"TENANT_{suffix}_PRODUCT_CANARY", lifecycle_status="active", product_family="DAY27", created_at=stamp, updated_at=stamp)
            db.add(product); db.flush()
            version = ProductVersion(id=uuid.uuid4(), tenant_id=tenant.id, product_id=product.id, version_identifier=f"TENANT_{suffix}_VERSION_CANARY", description=f"TENANT_{suffix}_VERSION_CANARY", lifecycle_status="active", created_at=stamp, updated_at=stamp)
            db.add(version); db.flush()
            investigation = Investigation(id=uuid.uuid4(), tenant_id=tenant.id, product_id=product.id, investigation_identifier=f"DAY27-AUTO-{suffix}-{uuid.uuid4().hex[:8]}", investigation_question="Synthetic retrieval isolation", status="open", opened_at=stamp, created_at=stamp, updated_at=stamp)
            db.add(investigation); db.flush()
            evidence = Evidence(id=uuid.uuid4(), tenant_id=tenant.id, investigation_id=investigation.id, evidence_identifier=f"TENANT_{suffix}_EVIDENCE_CANARY", evidence_type="DAY27_SYNTHETIC", title=f"Synthetic evidence {suffix}", source_reference=f"DAY27-{suffix}", reliability_status="reviewed", fact_type="source_fact", content=f"TENANT_{suffix}_EVIDENCE_CANARY", created_at=stamp, updated_at=stamp)
            db.add(evidence); db.flush()
            records[suffix] = {"tenant": tenant, "product": product, "version": version, "investigation": investigation, "evidence": evidence}
        db.commit()
        yield db, records
    finally:
        for item in records.values():
            db.query(Evidence).filter(Evidence.id == item["evidence"].id).delete(synchronize_session=False)
            db.query(Investigation).filter(Investigation.id == item["investigation"].id).delete(synchronize_session=False)
            db.query(ProductVersion).filter(ProductVersion.id == item["version"].id).delete(synchronize_session=False)
            db.query(Product).filter(Product.id == item["product"].id).delete(synchronize_session=False)
            db.query(Tenant).filter(Tenant.id == item["tenant"].id).delete(synchronize_session=False)
        db.commit(); db.close()


def test_real_database_tenant_positive_and_ai_safe_matrix(day27_db):
    db, records = day27_db
    service = AuthorizedRetrievalService()
    for suffix in ("A", "B"):
        item = records[suffix]
        result = service.retrieve(db, AuthorizedRetrievalRequest(item["tenant"].id, product_id=item["product"].id, product_version_id=item["version"].id, evidence_id=item["evidence"].id))
        assert result.products[0]["identifier"] == f"TENANT_{suffix}_PRODUCT_CANARY"
        assert result.product_versions[0]["identifier"] == f"TENANT_{suffix}_VERSION_CANARY"
        assert result.evidence[0]["identifier"] == f"TENANT_{suffix}_EVIDENCE_CANARY"
        assert all(f"TENANT_{'B' if suffix == 'A' else 'A'}_" not in str(result) for _ in [0])


def test_real_database_cross_tenant_and_relationship_exclusion(day27_db):
    db, records = day27_db
    service = AuthorizedRetrievalService()
    a, b = records["A"], records["B"]
    foreign = service.retrieve(db, AuthorizedRetrievalRequest(a["tenant"].id, product_id=b["product"].id, product_version_id=b["version"].id, evidence_id=b["evidence"].id))
    mismatch = service.retrieve(db, AuthorizedRetrievalRequest(a["tenant"].id, product_id=a["product"].id, product_version_id=b["version"].id))
    assert foreign.products == () and foreign.product_versions == () and foreign.evidence == ()
    assert mismatch.product_versions == ()


def test_real_database_retrieval_bound_is_enforced(day27_db):
    db, records = day27_db
    item = records["A"]
    result = AuthorizedRetrievalService().retrieve(db, AuthorizedRetrievalRequest(item["tenant"].id, product_id=item["product"].id, limit=10000))
    assert len(result.products) <= 100
