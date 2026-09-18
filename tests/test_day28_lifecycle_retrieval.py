from datetime import datetime, timezone
from uuid import uuid4

import pytest

from ask_mdarix.lifecycle_retrieval import LifecycleRetrievalRequest, LifecycleRetrievalService
from backend.app.db.models.foundation import (
    Complaint, Component, ComponentSupplier, Evidence, Investigation,
    InvestigationComplaint, InvestigationEvidence, Product, ProductComponent,
    ProductVersion, Supplier, Tenant,
)
from backend.app.db.session import SessionLocal


@pytest.fixture()
def lifecycle_fixture():
    db = SessionLocal()
    now = datetime.now(timezone.utc)
    suffix = uuid4().hex[:10]
    a = Tenant(id=uuid4(), tenant_key=f"DAY28_TEST_A_{suffix}", name="Day 28 Test A", status="active", created_at=now, updated_at=now)
    b = Tenant(id=uuid4(), tenant_key=f"DAY28_TEST_B_{suffix}", name="Day 28 Test B", status="active", created_at=now, updated_at=now)
    db.add_all([a, b]); db.flush()
    rows = []
    for tenant, label in ((a, "A"), (b, "B")):
        product = Product(id=uuid4(), tenant_id=tenant.id, product_identifier=f"DAY28_{label}_PRODUCT", name=f"Day 28 Product {label}", lifecycle_status="active", created_at=now, updated_at=now)
        version = ProductVersion(id=uuid4(), tenant_id=tenant.id, product_id=product.id, version_identifier=f"DAY28_{label}_VERSION", lifecycle_status="active", created_at=now, updated_at=now)
        component = Component(id=uuid4(), tenant_id=tenant.id, component_identifier=f"DAY28_{label}_COMPONENT", name=f"Component {label}", status="active", created_at=now, updated_at=now)
        supplier = Supplier(id=uuid4(), tenant_id=tenant.id, supplier_identifier=f"DAY28_{label}_SUPPLIER", name=f"Supplier {label}", status="active", created_at=now, updated_at=now)
        investigation = Investigation(id=uuid4(), tenant_id=tenant.id, product_id=product.id, investigation_identifier=f"DAY28_{label}_INVESTIGATION", investigation_question="bounded lifecycle retrieval", status="open", created_at=now, updated_at=now)
        complaint = Complaint(id=uuid4(), tenant_id=tenant.id, complaint_identifier=f"DAY28_{label}_COMPLAINT", product_id=product.id, product_version_id=version.id, description="synthetic complaint", status="open", created_at=now, updated_at=now)
        evidence = Evidence(id=uuid4(), tenant_id=tenant.id, investigation_id=investigation.id, evidence_identifier=f"DAY28_{label}_EVIDENCE", evidence_type="TEST", title="Synthetic evidence", reliability_status="reviewed", content="safe source fact", created_at=now, updated_at=now)
        # Flush parent rows in dependency order so composite tenant/product FKs
        # are exercised exactly as they are in the live schema.
        db.add_all([product, component, supplier]); db.flush()
        db.add(version); db.flush()
        db.add(investigation); db.flush()
        db.add(complaint); db.flush()
        db.add(evidence); db.flush()
        db.add_all([ProductComponent(tenant_id=tenant.id, product_version_id=version.id, component_id=component.id, relationship_status="active", created_at=now), ComponentSupplier(tenant_id=tenant.id, component_id=component.id, supplier_id=supplier.id, created_at=now), InvestigationComplaint(tenant_id=tenant.id, investigation_id=investigation.id, complaint_id=complaint.id, created_at=now), InvestigationEvidence(tenant_id=tenant.id, investigation_id=investigation.id, evidence_id=evidence.id, relevance="supporting", created_at=now)])
        rows.append((tenant, product, version, component, supplier, investigation, complaint, evidence))
    db.commit()
    try:
        yield db, rows
    finally:
        tenant_ids = [row[0].id for row in rows]
        for model in (InvestigationEvidence, InvestigationComplaint, ComponentSupplier, ProductComponent):
            db.query(model).filter(model.tenant_id.in_(tenant_ids)).delete(synchronize_session=False)
        for model in (Evidence, Complaint, Investigation, Supplier, Component, ProductVersion, Product, Tenant):
            ids = [getattr(row[i], "id") for row in rows for i in range(8) if isinstance(row[i], model)]
            if ids:
                db.query(model).filter(model.id.in_(ids)).delete(synchronize_session=False)
        db.commit(); db.close()


def test_day28_positive_relationships_and_provenance(lifecycle_fixture):
    db, rows = lifecycle_fixture
    tenant, product, version, component, supplier, investigation, complaint, evidence = rows[0]
    result = LifecycleRetrievalService().retrieve(db, LifecycleRetrievalRequest(tenant_id=tenant.id, product_version_id=version.id, complaint_id=complaint.id, investigation_id=investigation.id, evidence_id=evidence.id))
    assert result["products"][0]["id"] == str(product.id)
    assert result["product_versions"][0]["product_id"] == str(product.id)
    assert result["components"][0]["id"] == str(component.id)
    assert result["suppliers"][0]["id"] == str(supplier.id)
    assert result["evidence"][0]["source_reference"] is None
    assert all("caus" not in str(rel).lower() for rel in result["relationships"])
    assert result["ai_safe_context"]
    assert all("tenant_id" not in item["record"] for item in result["ai_safe_context"])


def test_day28_cross_tenant_and_wrong_product_version_are_empty(lifecycle_fixture):
    db, rows = lifecycle_fixture
    tenant_a, product_a, version_a, component_a, supplier_a, investigation_a, complaint_a, evidence_a = rows[0]
    tenant_b, product_b, version_b, component_b, supplier_b, investigation_b, complaint_b, evidence_b = rows[1]
    service = LifecycleRetrievalService()
    foreign = service.retrieve(db, LifecycleRetrievalRequest(tenant_id=tenant_a.id, product_id=product_b.id, product_version_id=version_b.id))
    mismatch = service.retrieve(db, LifecycleRetrievalRequest(tenant_id=tenant_a.id, product_id=product_a.id, product_version_id=version_b.id))
    foreign_lifecycle = service.retrieve(db, LifecycleRetrievalRequest(
        tenant_id=tenant_a.id,
        product_version_id=version_a.id,
        complaint_id=complaint_b.id,
        investigation_id=investigation_b.id,
        evidence_id=evidence_b.id,
    ))
    assert foreign["products"] == [] and foreign["product_versions"] == []
    assert mismatch["product_versions"] == []
    assert foreign_lifecycle["complaints"] == []
    assert foreign_lifecycle["investigations"] == []
    assert foreign_lifecycle["evidence"] == []
    assert all(str(item["id"]) not in {str(component_b.id), str(supplier_b.id)} for item in foreign_lifecycle["components"] + foreign_lifecycle["suppliers"])


def test_day28_bounded_retrieval_metadata(lifecycle_fixture):
    db, rows = lifecycle_fixture
    tenant, product, version, *_ = rows[0]
    result = LifecycleRetrievalService().retrieve(db, LifecycleRetrievalRequest(tenant_id=tenant.id, product_id=product.id, product_version_id=version.id, limit=10000))
    assert result["retrieval_metadata"]["bounded_limit"] == 100
    assert result["retrieval_metadata"]["tenant_scoped"] is True
