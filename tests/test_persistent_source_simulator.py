from fastapi.testclient import TestClient
from uuid import uuid4

from source_simulator import persistent_app


def test_persistent_provider_requires_token_and_enforces_tenant_scope():
    client = TestClient(persistent_app.app)
    assert client.get("/ready").status_code == 200
    assert client.get("/records/Complaint").status_code == 401
    assert client.get("/records/Complaint", headers={"X-Provider-Token": "sim-a"}, params={"tenant": "TENANT_B"}).status_code == 403


def test_persistent_provider_writes_reads_and_versions_records():
    client = TestClient(persistent_app.app)
    headers = {"X-Provider-Token": "sim-a"}
    external_id = f"CMP-{uuid4()}"
    first = client.post("/records/Complaint", headers=headers, json={"external_id": external_id, "record_version": "1", "payload": {"severity": "LOW"}})
    second = client.post("/records/Complaint", headers=headers, json={"external_id": external_id, "record_version": "2", "payload": {"severity": "HIGH"}})
    assert first.status_code == second.status_code == 200
    assert client.get("/records/Complaint", headers=headers).json()["records"][0]["severity"] == "HIGH"
    assert len(client.get(f"/records/Complaint/{external_id}/history", headers=headers).json()["history"]) == 1
