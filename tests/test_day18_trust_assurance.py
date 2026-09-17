from fastapi.testclient import TestClient
from backend.app.main import app

EXECUTION = "4fb11c6f-e952-4eca-ab6b-5d040d4e2270"

def test_assurance_persists_profile_and_checks():
    response = TestClient(app).post(f"/api/v1/ai-executions/{EXECUTION}/assurance", json={"output_type": "AI_INVESTIGATOR"})
    assert response.status_code == 200
    body = response.json()
    assert body["trust_policy_version"] == "MDARIX_AI_TRUST_POLICY_R1_V1"
    assert body["configuration_hash"] and len(body["configuration_hash"]) == 64
    assert len(body["checks"]) >= 5
    assert body["human_review_required"] is True

def test_foreign_execution_is_not_available():
    response = TestClient(app).get("/api/v1/ai-executions/00000000-0000-0000-0000-000000000000/assurance")
    assert response.status_code == 404
