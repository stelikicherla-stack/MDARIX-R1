from fastapi.testclient import TestClient

from backend.app.main import app
from tests.conftest import authenticated_client

INVESTIGATION_ID = "5a541092-f384-44eb-a832-3137749e7393"

def test_brief_generation_is_versioned_and_grounded():
    client = authenticated_client(app)
    first = client.post(f"/api/v1/investigations/{INVESTIGATION_ID}/briefs", json={"temporal_mode": "current"})
    assert first.status_code == 200
    payload = first.json()
    assert payload["status"] == "GENERATED"
    assert payload["content"]["not_established"]
    assert payload["provenance"]["ground_truth_references"] == []
    second = client.post(f"/api/v1/investigations/{INVESTIGATION_ID}/briefs", json={"temporal_mode": "known", "as_of": "2026-02-15T00:00:00Z"})
    assert second.status_code == 200
    assert second.json()["brief_version"] > payload["brief_version"]
    latest = client.get(f"/api/v1/investigations/{INVESTIGATION_ID}/briefs/latest")
    assert latest.status_code == 200
    assert latest.json()["id"] == second.json()["id"]

def test_brief_rejects_foreign_investigation():
    client = authenticated_client(app)
    response = client.get("/api/v1/investigations/00000000-0000-0000-0000-000000000000/briefs/latest")
    assert response.status_code == 404
