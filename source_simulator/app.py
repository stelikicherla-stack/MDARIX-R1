"""Standalone, deterministic source-system simulator.

This app deliberately has no dependency on the MDARIX database or request
context. It represents an untrusted external provider for local integration
tests only.
"""
from fastapi import FastAPI, Header, HTTPException, Query

app = FastAPI(title="MDARIX External Source Simulator", version="1.0.0")

FAULTS: dict[str, str] = {}

COMPLAINT_FIELDS = [
    {"name": "complaint_id", "data_type": "string", "required": True, "nullable": False},
    {"name": "complaint_number", "data_type": "string", "required": True, "nullable": False},
    {"name": "product_code", "data_type": "string", "required": True, "nullable": False},
    {"name": "product_revision", "data_type": "string", "required": False, "nullable": True},
    {"name": "event_date", "data_type": "date", "required": False, "nullable": True},
    {"name": "severity", "data_type": "string", "required": False, "nullable": True, "enum_values": ["LOW", "MEDIUM", "HIGH"]},
    {"name": "status", "data_type": "string", "required": True, "nullable": False, "enum_values": ["OPEN", "CLOSED"]},
]
COMPLAINTS = [{"complaint_id": "SIM-CMP-001", "complaint_number": "CMP-001", "product_code": "AF100", "product_revision": "D", "event_date": "2026-01-01", "severity": "MEDIUM", "status": "OPEN"}]

TENANT_KEYS = {"TENANT_A", "TENANT_B", "TENANT_C", "TENANT_D"}

def _tenant_key(header: str | None, query: str | None) -> str:
    """Resolve simulator tenancy explicitly; defaults only for legacy tests."""
    value = (header or query or "TENANT_A").strip().upper()
    if value not in TENANT_KEYS:
        raise HTTPException(404, detail="TENANT_NOT_FOUND")
    return value

def _tenant_record(record: dict, tenant: str) -> dict:
    result = dict(record)
    # Canary values make accidental cross-tenant reads immediately visible.
    for key, value in list(result.items()):
        if tenant != "TENANT_A" and isinstance(value, str) and (key.endswith("_id") or key.endswith("_number") or key in {"product_code", "product_name"}):
            result[key] = f"{value}-{tenant}"
    result["tenant_key"] = tenant
    return result

def _tenant_records(record, tenant: str):
    values = record if isinstance(record, list) else [record]
    return [_tenant_record(item, tenant) for item in values]

CATALOG = {
    "plm": {
        "products": {"product_id": "SIM-PROD-001", "product_code": "AF100", "product_name": "AsterFlow 100", "product_family": "Controller", "product_type": "DEVICE", "lifecycle_status": "ACTIVE", "manufacturer_name": "MDARIX Synthetic", "market_name": "GLOBAL", "record_version": "1"},
        "product-versions": {"version_id": "SIM-PV-001", "product_id": "SIM-PROD-001", "revision": "D", "version_name": "Version D", "effective_date": "2026-01-01", "release_date": "2026-01-02", "status": "RELEASED", "record_version": "1"},
        "components": {"component_id": "SIM-COMP-001", "component_number": "CTRL-100", "component_name": "Controller", "revision": "D", "product_version_id": "SIM-PV-001", "quantity": 1, "status": "ACTIVE"},
        "changes": {"change_id": "SIM-CHG-001", "change_number": "CHG-001", "change_type": "DESIGN", "title": "Synthetic design change", "status": "APPROVED"},
    },
    "erp": {
        "suppliers": {"vendor_id": "SIM-SUP-001", "vendor_code": "SUP-001", "vendor_name": "Synthetic Supplier", "country": "US", "status": "ACTIVE", "qualification_status": "QUALIFIED"},
        "sites": {"plant_id": "SIM-SITE-001", "plant_code": "SITE-001", "plant_name": "Synthetic Plant", "country": "US", "status": "ACTIVE"},
        "lots": {"lot_id": "SIM-LOT-001", "lot_number": "LOT-001", "product_id": "SIM-PROD-001", "product_version": "D", "plant_id": "SIM-SITE-001", "status": "RELEASED", "traceability_status": "COMPLETE"},
    },
    "qms": {
        "complaints": COMPLAINTS[0],
        "investigations": {"investigation_id": "SIM-INV-001", "investigation_number": "INV-001", "title": "Synthetic investigation", "question": "What changed?", "complaint_ids": ["SIM-CMP-001"], "status": "OPEN"},
        "capas": {"capa_id": "SIM-CAPA-001", "capa_number": "CAPA-001", "title": "Synthetic CAPA", "status": "OPEN"},
        "evidence": {"evidence_id": "SIM-EVD-001", "document_number": "DOC-001", "title": "Synthetic evidence", "checksum": "synthetic-checksum", "status": "ACTIVE"},
    },
    "risk": {
        "risks": {"risk_id": "SIM-RISK-001", "risk_number": "RISK-001", "product_id": "SIM-PROD-001", "risk_level": "MEDIUM", "status": "OPEN"},
        "failure-modes": {"failure_mode_id": "SIM-FM-001", "failure_mode_code": "FM-001", "name": "Synthetic failure", "status": "OPEN"},
        "controls": {"control_id": "SIM-CTL-001", "control_number": "CTL-001", "risk_id": "SIM-RISK-001", "status": "ACTIVE"},
    },
    "crm": {"cases": {"case_id": "SIM-CASE-001", "case_number": "CASE-001", "product_code": "AF100", "subject": "Synthetic case", "status": "OPEN"}},
    "rim": {"vigilance-assessments": {"assessment_id": "SIM-VA-001", "complaint_id": "SIM-CMP-001", "jurisdiction": "US", "status": "PENDING"}},
    "safety": {"field-actions": {"action_id": "SIM-FA-001", "action_number": "FA-001", "product_id": "SIM-PROD-001", "status": "OPEN"}},
    "lims": {"results": {"result_id": "SIM-RES-001", "sample_id": "SIM-SAMPLE-001", "test_name": "Synthetic test", "result_status": "PASS"}},
    "mes": {"production-records": {"production_record_id": "SIM-PR-001", "lot_number": "LOT-001", "product_code": "AF100", "process_status": "COMPLETE"}},
}

def _fault(domain: str):
    value = FAULTS.get(domain) or FAULTS.get("*")
    if value == "unavailable": raise HTTPException(503, detail="SIMULATED_UNAVAILABLE")
    if value in {"401", "403", "429", "500"}: raise HTTPException(int(value), detail=f"SIMULATED_{value}")

def _fields(record: dict):
    return [{"name": key, "data_type": "boolean" if isinstance(value, bool) else "integer" if isinstance(value, int) else "string", "required": key.endswith("_id") or key in {"status", "record_version"}, "nullable": False} for key, value in record.items()]

@app.get("/health")
def health():
    return {"status": "ok", "provider": "MDARIX_EXTERNAL_SOURCE_SIMULATOR", "contract_version": "v1"}

@app.get("/ready")
def ready():
    return {"status": "ready", "provider": "MDARIX_EXTERNAL_SOURCE_SIMULATOR"}

@app.get("/api/v1/schema/{source_object}")
def schema(source_object: str, tenant: str | None = Query(None), x_simulator_tenant: str | None = Header(None)):
    tenant_key = _tenant_key(x_simulator_tenant, tenant)
    if source_object.upper() != "COMPLAINT":
        return {"source_object": source_object, "schema_version": "v1", "fields": []}
    return {"source_application": "TRACKWISE_SIMULATOR", "source_object": "COMPLAINT", "schema_version": "v1", "tenant_key": tenant_key, "fields": COMPLAINT_FIELDS}

@app.get("/api/v1/trackwise/complaints")
def complaints(tenant: str | None = Query(None), x_simulator_tenant: str | None = Header(None)):
    tenant_key = _tenant_key(x_simulator_tenant, tenant)
    return {"source_application": "TRACKWISE_SIMULATOR", "source_object": "COMPLAINT", "schema_version": "v1", "tenant_key": tenant_key, "records": _tenant_records(COMPLAINTS, tenant_key)}

@app.post("/api/v1/faults")
def set_fault(domain: str, mode: str = ""):
    if mode and mode not in {"unavailable", "401", "403", "429", "500"}: raise HTTPException(422, detail="Unsupported fault mode")
    if mode: FAULTS[domain.lower()] = mode
    else: FAULTS.pop(domain.lower(), None)
    return {"domain": domain.lower(), "mode": FAULTS.get(domain.lower())}

@app.get("/api/{domain}/v1/{source_object}")
def source_records(domain: str, source_object: str, limit: int = Query(100, ge=1, le=500), cursor: int = Query(0, ge=0), since: str | None = None, tenant: str | None = Query(None), x_simulator_tenant: str | None = Header(None)):
    domain, source_object = domain.lower(), source_object.lower()
    tenant_key = _tenant_key(x_simulator_tenant, tenant)
    _fault(domain)
    record = CATALOG.get(domain, {}).get(source_object)
    if record is None: raise HTTPException(404, detail="SOURCE_OBJECT_NOT_FOUND")
    records = _tenant_records(record, tenant_key)
    page = records[cursor:cursor + limit]
    return {"source_application": f"{domain.upper()}_SIMULATOR", "source_object": source_object, "schema_version": "v1", "tenant_key": tenant_key, "records": page, "next_cursor": cursor + limit if cursor + limit < len(records) else None, "since": since}

@app.get("/api/{domain}/v1/schema/{source_object}")
def source_schema(domain: str, source_object: str, tenant: str | None = Query(None), x_simulator_tenant: str | None = Header(None)):
    domain, source_object = domain.lower(), source_object.lower(); _fault(domain); tenant_key = _tenant_key(x_simulator_tenant, tenant)
    record = CATALOG.get(domain, {}).get(source_object)
    if record is None: raise HTTPException(404, detail="SOURCE_OBJECT_NOT_FOUND")
    sample = record[0] if isinstance(record, list) else record
    return {"source_application": f"{domain.upper()}_SIMULATOR", "source_object": source_object, "schema_version": "v1", "tenant_key": tenant_key, "fields": _fields(sample)}
