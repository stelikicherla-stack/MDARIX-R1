from fastapi.testclient import TestClient

from source_simulator.app import app


def test_source_simulator_health_and_schema_are_external_contracts():
    client = TestClient(app)
    assert client.get("/health").json()["provider"] == "MDARIX_EXTERNAL_SOURCE_SIMULATOR"
    payload = client.get("/api/v1/schema/COMPLAINT").json()
    assert payload["schema_version"] == "v1"
    assert {field["name"] for field in payload["fields"]} >= {"complaint_number", "product_code"}


def test_source_simulator_returns_untrusted_sample_records():
    response = TestClient(app).get("/api/v1/trackwise/complaints")
    assert response.status_code == 200
    assert response.json()["records"][0]["complaint_id"] == "SIM-CMP-001"


def test_source_simulator_exposes_versioned_domains_and_pagination():
    client = TestClient(app)
    response = client.get("/api/plm/v1/products", params={"limit": 1, "cursor": 0})
    assert response.status_code == 200
    assert response.json()["records"][0]["product_id"] == "SIM-PROD-001"
    schema = client.get("/api/qms/v1/schema/complaints")
    assert schema.status_code == 200
    assert schema.json()["schema_version"] == "v1"


def test_source_simulator_fault_profile_is_explicit_and_resettable():
    client = TestClient(app)
    assert client.post("/api/v1/faults", params={"domain": "plm", "mode": "429"}).status_code == 200
    assert client.get("/api/plm/v1/products").status_code == 429
    assert client.post("/api/v1/faults", params={"domain": "plm"}).json()["mode"] is None
    assert client.get("/api/plm/v1/products").status_code == 200


def test_source_simulator_partitions_records_by_explicit_tenant():
    client = TestClient(app)
    a = client.get("/api/plm/v1/products", params={"tenant": "TENANT_A"})
    b = client.get("/api/plm/v1/products", headers={"X-Simulator-Tenant": "TENANT_B"})
    assert a.status_code == b.status_code == 200
    assert a.json()["tenant_key"] == "TENANT_A"
    assert b.json()["tenant_key"] == "TENANT_B"
    assert a.json()["records"][0]["product_id"] != b.json()["records"][0]["product_id"]
    assert a.json()["records"][0]["tenant_key"] != b.json()["records"][0]["tenant_key"]


def test_source_simulator_rejects_unknown_tenant_and_exposes_readiness():
    client = TestClient(app)
    assert client.get("/ready").json()["status"] == "ready"
    assert client.get("/api/plm/v1/products", params={"tenant": "TENANT_X"}).status_code == 404
