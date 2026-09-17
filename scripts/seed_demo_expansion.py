"""Add synthetic demo records for interactive Product 360 and investigation testing.

This is idempotent: it only adds the MDARIX-DEMO product set when absent and
never alters the canonical Golden dataset or its evaluation scenarios.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.db.models.foundation import (
    Complaint, Component, ComponentSupplier, Evidence, Investigation, InvestigationComplaint,
    InvestigationEvidence, LotBatch, ManufacturingSite, Product, ProductComponent,
    ProductVersion, Supplier, Tenant,
)
from backend.app.db.session import SessionLocal


NOW = datetime.now(timezone.utc)
PRODUCTS = [
    ("PRD-ORBIT-300", "OrbitCare 300 Infusion Pump", "Infusion therapy", "pressure-alarm"),
    ("PRD-PULSE-410", "PulseWatch 410 Monitor", "Patient monitoring", "signal-dropout"),
    ("PRD-VENTRA-250", "VentraLink 250 Respiratory Controller", "Respiratory support", "flow-variance"),
]


def stamp(offset: int = 0) -> dict:
    value = NOW - timedelta(days=offset)
    return {"source_timestamp": value, "effective_timestamp": value, "recorded_timestamp": value,
            "ingestion_timestamp": value, "created_at": value, "updated_at": value}


def run() -> None:
    db = SessionLocal()
    try:
        tenant = db.query(Tenant).filter(Tenant.tenant_key == "ACME_CARE_SYNTHETIC").first() or db.query(Tenant).first()
        if not tenant:
            raise RuntimeError("No tenant exists. Run the standard MDARIX seed first.")
        site = db.query(ManufacturingSite).filter(ManufacturingSite.tenant_id == tenant.id).first()
        if not site:
            site = ManufacturingSite(id=uuid.uuid4(), tenant_id=tenant.id, site_identifier="DEMO-MFG-01", name="Demo Assembly Site", location="Synthetic", status="active", source_system="DEMO", source_identifier="DEMO-MFG-01", **stamp(240))
            db.add(site)

        created = 0
        for product_index, (identifier, name, family, symptom) in enumerate(PRODUCTS, 1):
            if db.query(Product).filter(Product.tenant_id == tenant.id, Product.product_identifier == identifier).first():
                continue
            product = Product(id=uuid.uuid4(), tenant_id=tenant.id, product_identifier=identifier, name=name,
                              description=f"Synthetic demo product for {family.lower()} workflow testing.", lifecycle_status="active",
                              product_family=family, manufacturer_context="AcmeCare Instruments (synthetic)",
                              source_system="DEMO", source_identifier=identifier, **stamp(180 - product_index))
            db.add(product)
            db.flush()
            versions = []
            for revision, age in (("Rev A", 150), ("Rev B", 75)):
                version = ProductVersion(id=uuid.uuid4(), tenant_id=tenant.id, product_id=product.id, version_identifier=revision,
                                         description=f"{name} {revision} synthetic configuration", lifecycle_status="active",
                                         release_timestamp=NOW - timedelta(days=age), source_system="DEMO", source_identifier=f"{identifier}-{revision[-1]}", **stamp(age))
                db.add(version); versions.append(version)
            supplier = Supplier(id=uuid.uuid4(), tenant_id=tenant.id, supplier_identifier=f"DEMO-SUP-{product_index:02d}", name=f"Demo Supplier {product_index}", status="active", source_system="DEMO", source_identifier=f"DEMO-SUP-{product_index:02d}", **stamp(160))
            db.add(supplier)
            db.flush()
            components = []
            for component_index, label in enumerate(("Control Board", "Sensor Assembly", "Power Module"), 1):
                component = Component(id=uuid.uuid4(), tenant_id=tenant.id, component_identifier=f"{identifier}-C{component_index}", name=f"{name} {label}", revision="Rev B", description="Synthetic demo configuration component.", status="active", source_system="DEMO", source_identifier=f"{identifier}-C{component_index}", **stamp(120 - component_index))
                db.add(component); components.append(component)
            db.flush()
            for component in components:
                db.add(ComponentSupplier(id=uuid.uuid4(), tenant_id=tenant.id, component_id=component.id, supplier_id=supplier.id, effective_timestamp=NOW - timedelta(days=120), created_at=NOW))
            for component in components:
                db.add(ProductComponent(id=uuid.uuid4(), tenant_id=tenant.id, product_version_id=versions[-1].id, component_id=component.id, relationship_status="active", effective_timestamp=NOW - timedelta(days=75), created_at=NOW))

            lots = []
            for lot_index in range(1, 5):
                lot = LotBatch(id=uuid.uuid4(), tenant_id=tenant.id, lot_identifier=f"{identifier}-LOT-{lot_index:03d}", product_version_id=versions[-1].id, manufacturing_site_id=site.id, status="active", source_system="DEMO", source_identifier=f"{identifier}-LOT-{lot_index:03d}", **stamp(60 - lot_index))
                db.add(lot); lots.append(lot)

            investigations = []
            for investigation_index, question in enumerate((
                f"Why did {symptom.replace('-', ' ')} reports increase after Rev B?",
                f"Which {identifier} lots share the current component configuration?",
                f"What evidence is still needed before closing the {symptom.replace('-', ' ')} review?",
            ), 1):
                investigation = Investigation(id=uuid.uuid4(), tenant_id=tenant.id, product_id=product.id,
                                                investigation_identifier=f"DEMO-INV-{product_index:02d}{investigation_index}", investigation_question=question,
                                                status="open" if investigation_index != 2 else "closed", opened_at=NOW - timedelta(days=20 - investigation_index),
                                                closed_at=(NOW - timedelta(days=8)) if investigation_index == 2 else None,
                                                owner_ref="demo.quality@mdarix.local", source_system="DEMO", source_identifier=f"DEMO-INV-{product_index:02d}{investigation_index}", **stamp(20 - investigation_index))
                db.add(investigation); investigations.append(investigation)
            db.flush()
            complaint_links = []
            for complaint_index in range(1, 6):
                complaint = Complaint(id=uuid.uuid4(), tenant_id=tenant.id, complaint_identifier=f"{identifier}-CMP-{complaint_index:03d}", product_id=product.id, product_version_id=versions[-1].id, lot_batch_id=lots[(complaint_index - 1) % len(lots)].id, description=f"Synthetic {symptom} observation {complaint_index} for interactive testing.", status="open", source_system="DEMO", source_identifier=f"{identifier}-CMP-{complaint_index:03d}", **stamp(35 - complaint_index))
                db.add(complaint)
                complaint_links.append((investigations[(complaint_index - 1) % len(investigations)].id, complaint.id))
            db.flush()
            for investigation_id, complaint_id in complaint_links:
                db.add(InvestigationComplaint(id=uuid.uuid4(), tenant_id=tenant.id, investigation_id=investigation_id, complaint_id=complaint_id, created_at=NOW))
            evidence_links = []
            for evidence_index, investigation in enumerate(investigations, 1):
                evidence = Evidence(id=uuid.uuid4(), tenant_id=tenant.id, evidence_identifier=f"{identifier}-EV-{evidence_index:03d}", investigation_id=investigation.id, evidence_type="demo_record", title=f"{name} investigation evidence {evidence_index}", source_reference="MDARIX synthetic demo data", document_ref="demo://synthetic", reliability_status="validated", fact_type="source_fact", content="Synthetic test evidence. It provides context only and does not establish causality.", source_system="DEMO", source_identifier=f"{identifier}-EV-{evidence_index:03d}", **stamp(15 - evidence_index))
                db.add(evidence)
                evidence_links.append((investigation.id, evidence.id))
            db.flush()
            for investigation_id, evidence_id in evidence_links:
                db.add(InvestigationEvidence(id=uuid.uuid4(), tenant_id=tenant.id, investigation_id=investigation_id, evidence_id=evidence_id, relevance="Synthetic demo evidence for UI testing.", created_at=NOW))
            created += 1
        db.commit()
        print(f"Demo expansion complete: {created} product sets added.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()
