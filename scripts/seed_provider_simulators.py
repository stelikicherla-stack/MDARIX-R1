"""Seed the four isolated provider simulators with tenant-partitioned data.

This only writes to local Docker simulator APIs; it never writes customer systems.
"""
import json
import os
import sys
from urllib.request import Request, urlopen

ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, ROOT)
from source_simulator.provider_catalog import PROVIDER_CATALOG, PROVIDER_PORTS

TENANTS = {"TENANT_A": "sim-a", "TENANT_B": "sim-b", "TENANT_C": "sim-c", "TENANT_D": "sim-d"}
SEEDS = {
    "TRACKWISE": {"Complaint": {"complaint_number": "CMP-{tenant}-001", "opened_date": "2026-09-01T10:00:00Z", "severity": "major", "status": "OPEN"}, "Investigation": {"investigation_number": "INV-{tenant}-001", "opened_date": "2026-09-01T11:00:00Z", "status": "OPEN"}, "CAPA": {"capa_number": "CAPA-{tenant}-001", "opened_date": "2026-09-01T12:00:00Z", "status": "OPEN"}},
    "PLM": {"Product": {"product_number": "PRD-{tenant}-001", "name": "AsterFlow Controller", "status": "ACTIVE"}, "ProductVersion": {"product_number": "PRD-{tenant}-001", "version": "D", "release_date": "2026-08-15T00:00:00Z"}, "Component": {"component_number": "CMPNT-{tenant}-001", "name": "Control Module", "status": "ACTIVE"}, "Change": {"change_number": "CHG-{tenant}-001", "effective_date": "2026-08-20T00:00:00Z", "status": "RELEASED"}},
    "ERP": {"Supplier": {"supplier_number": "SUP-{tenant}-001", "name": "Northwind Medical", "status": "ACTIVE"}, "Site": {"site_number": "SITE-{tenant}-001", "name": "Primary Manufacturing Site", "status": "ACTIVE"}, "Lot": {"lot_number": "LOT-{tenant}-001", "product_number": "PRD-{tenant}-001", "status": "RELEASED"}},
    "SUPPLIER": {"SupplierPart": {"part_number": "PART-{tenant}-001", "description": "Validated controller part", "status": "ACTIVE"}, "Certificate": {"certificate_number": "CERT-{tenant}-001", "expiry_date": "2027-09-01T00:00:00Z", "status": "VALID"}, "SupplierEvent": {"event_number": "SE-{tenant}-001", "event_date": "2026-09-02T09:00:00Z", "event_type": "QUALITY_REVIEW"}},
}

def call(url, token, method="GET", body=None):
    data = None if body is None else json.dumps(body).encode()
    req = Request(url, data=data, method=method, headers={"X-Provider-Token": token, "Content-Type": "application/json"})
    with urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode())

def main():
    total = 0
    for provider, entities in SEEDS.items():
        base = f"http://127.0.0.1:{PROVIDER_PORTS[provider]}"
        for tenant, token in TENANTS.items():
            for entity, template in entities.items():
                payload = {key: value.format(tenant=tenant) for key, value in template.items()}
                external_id = next(iter(payload.values()))
                result = call(f"{base}/records/{entity}?tenant={tenant}", token, "POST", {"external_id": external_id, "record_version": "1", "payload": payload})
                total += 1
                if result["record"]["outcome"] not in {"CREATED", "UPDATED", "DUPLICATE"}:
                    raise RuntimeError(result)
    print(f"SEEDED {total} provider records across {len(TENANTS)} tenants")

if __name__ == "__main__":
    main()
