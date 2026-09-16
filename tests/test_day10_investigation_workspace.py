import datetime as dt

from fastapi.testclient import TestClient
from sqlalchemy import text

from backend.app.db.models.foundation import Investigation, Tenant
from backend.app.db.session import SessionLocal
from backend.app.main import app
from investigation_workspace.schemas import InvestigationWorkspaceRequest
from investigation_workspace.service import InvestigationWorkspaceService
from retrieval.service import TrustedRetrievalService


client = TestClient(app)


def ids():
    db = SessionLocal()
    try:
        tenant = db.query(Tenant).filter(Tenant.tenant_key == "ACME_CARE_SYNTHETIC").first()
        investigation = db.query(Investigation).filter(Investigation.tenant_id == tenant.id, Investigation.investigation_identifier == "INV-001").first()
        TrustedRetrievalService().index_evidence_chunks(db, tenant.id)
        return tenant.id, investigation.id
    finally:
        db.close()


def workspace(**updates):
    tenant_id, investigation_id = ids()
    request = InvestigationWorkspaceRequest(tenant_id=tenant_id, investigation_id=investigation_id, **updates)
    db = SessionLocal()
    try:
        return InvestigationWorkspaceService().workspace(db, request)
    finally:
        db.close()


def test_workspace_header_product_temporal_graph_and_evidence_context():
    view = workspace()
    assert view.investigation["investigation_identifier"] == "INV-001"
    assert view.product_context["product"]["product_identifier"] == "PRD-ASTER-100"
    assert view.temporal_context["event_time_distinct_from_known_time"] is True
    assert view.relationship_context["metadata"]["node_count"] >= 1
    assert view.evidence_context


def test_workspace_preserves_source_anchors_observations_and_entity_links():
    view = workspace()
    anchored = [chunk for evidence in view.evidence_context for chunk in evidence["chunks"] if chunk["source_anchor"]]
    assert anchored
    assert any(evidence["entity_links"] for evidence in view.evidence_context)
    assert all(evidence["fact_type"] != "ai_inference" for evidence in view.evidence_context)


def test_workspace_retrieval_context_has_score_semantics_not_causality():
    view = workspace(retrieval_top_k=5)
    assert view.retrieval_context is not None
    assert view.retrieval_context.status in {"COMPLETED", "NO_RELEVANT_EVIDENCE", "INSUFFICIENT_RELEVANT_EVIDENCE"}
    payload = view.model_dump_json().lower()
    assert "actual_root_cause" not in payload
    assert "retrieval relevance only" in payload
    assert view.guardrails["generates_causality"] is False


def test_workspace_known_as_of_excludes_late_available_evidence():
    as_of = dt.datetime(2026, 2, 15, tzinfo=dt.timezone.utc)
    known = workspace(temporal_mode="known", as_of=as_of)
    assert all(
        evidence["temporal"]["ingestion_timestamp"] is None
        or dt.datetime.fromisoformat(evidence["temporal"]["ingestion_timestamp"]) <= as_of
        for evidence in known.evidence_context
    )


def test_workspace_api_endpoint():
    _, investigation_id = ids()
    response = client.get(f"/api/v1/investigations/{investigation_id}/workspace", params={"retrieval_top_k": 5})
    assert response.status_code == 200
    payload = response.json()
    assert payload["metadata"]["workspace_version"] == "R1-Day10"
    assert payload["metadata"]["ground_truth_used"] is False
