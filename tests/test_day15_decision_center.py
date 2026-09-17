import uuid

from fastapi.testclient import TestClient
from sqlalchemy import text

from backend.app.db.session import engine
from backend.app.main import app
from decision_center.service import DecisionCenterService
from decision_center.schemas import DecisionContextRequest

client = TestClient(app)
service = DecisionCenterService()


def primary_investigation():
    with engine.connect() as conn:
        return conn.execute(text("SELECT id, tenant_id, product_id FROM investigations WHERE investigation_identifier='INV-001'")).one()


def test_decision_context_preserves_upstream_semantics_and_readiness():
    investigation, tenant_id, product_id = primary_investigation()
    context = service.context(__import__("backend.app.db.session", fromlist=["SessionLocal"]).SessionLocal(), tenant_id, investigation, DecisionContextRequest())
    assert context["investigation"]["identifier"] == "INV-001"
    assert context["product_context"]["product_id"] == str(product_id)
    assert context["readiness"]["state"] in {"INSUFFICIENT_EVIDENCE", "MATERIAL_UNKNOWNS_REMAIN", "CONTRADICTORY_EVIDENCE", "SUFFICIENT_FOR_REVIEW"}
    assert context["guardrails"]["human_decision_required"] is True
    assert context["guardrails"]["ground_truth_used"] is False


def test_decision_context_api_and_temporal_context():
    investigation, _, _ = primary_investigation()
    response = client.get(f"/api/v1/investigations/{investigation}/decision-context", params={"temporal_mode": "event", "as_of": "2026-02-15T00:00:00Z"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["temporal_context"]["mode"] == "event"
    assert payload["guardrails"]["ai_advisory_is_not_decision"] is True


def test_advisory_cannot_finalize_decision():
    investigation, _, _ = primary_investigation()
    response = client.post(f"/api/v1/investigations/{investigation}/decision-advisory", json={"temporal_mode": "current"})
    assert response.status_code == 200
    assert response.json()["advisory"]["human_authority_required"] is True
    assert "decision_status" not in response.json()["advisory"]


def test_human_decision_requires_rationale_and_review():
    investigation, _, _ = primary_investigation()
    missing = client.post(f"/api/v1/investigations/{investigation}/decisions", json={"selected_action": "NO_DECISION_YET", "authorized_by_ref": "reviewer", "temporal_mode": "current"})
    assert missing.status_code == 422
    created = client.post(f"/api/v1/investigations/{investigation}/decisions", json={"selected_action": "NO_DECISION_YET", "rationale": "Material unknowns remain; additional evidence is required.", "authorized_by_ref": "reviewer", "temporal_mode": "current"})
    assert created.status_code == 200
    decision_id = created.json()["id"]
    assert created.json()["decision_status"] == "REQUIRES_REVIEW"
    review = client.post(f"/api/v1/investigations/decisions/{decision_id}/reviews", json={"disposition": "APPROVED", "reviewer_ref": "reviewer", "comments": "Human review completed."})
    assert review.status_code == 200
    assert client.get(f"/api/v1/investigations/decisions/{decision_id}").json()["decision_status"] == "DECIDED"


def test_invalid_investigation_and_tenant_scoping():
    invalid = client.get(f"/api/v1/investigations/{uuid.uuid4()}/decision-context")
    assert invalid.status_code == 404
