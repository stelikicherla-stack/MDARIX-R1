from types import SimpleNamespace
from uuid import uuid4

from genai.grounding import advisory, build_authorized_context, source_provenance
from genai.provider import GenAIResult


class _Provider:
    def complete(self, prompt, context):
        assert "root cause" in prompt.lower()
        assert context["grounded_context"]["tenant_scope_enforced"] is True
        return GenAIResult("test", "safe-model", "v1", {"answer": "Review only"}, 10, 2, 0, 3)

    def audit_details(self, result):
        return {"provider": result.provider, "model": result.model, "human_review_required": True}


def test_context_is_tenant_scoped_fail_closed_and_excludes_sensitive_fields(monkeypatch):
    tenant_id, investigation_id = uuid4(), uuid4()
    payload = {
        "investigation": {"id": str(investigation_id), "investigation_question": "What changed?", "owner_ref": "hidden"},
        "product_context": {"product": {"id": "p1", "title": "Device", "password": "never"}},
        "temporal_context": {"mode": "current", "as_of": None},
        "relationship_context": {"relationships": []},
        "evidence_context": [{"evidence_identifier": "EV-1", "title": "Complaint", "source_reference": "TW-1", "token": "never", "content": "not allowlisted"}],
        "limitations": [],
    }
    monkeypatch.setattr(
        "genai.grounding.InvestigationWorkspaceService.workspace",
        lambda self, db, request: SimpleNamespace(model_dump=lambda mode: payload),
    )
    context = build_authorized_context(object(), tenant_id=tenant_id, investigation_id=investigation_id)
    serialized = str(context).lower()
    assert context["tenant_scope_enforced"] is True
    assert context["field_policy"] == "SERVER_ALLOWLIST_FAIL_CLOSED"
    assert "password" not in serialized and "token" not in serialized and "owner_ref" not in serialized
    assert context["evidence_context"][0]["evidence_identifier"] == "EV-1"
    assert source_provenance(context) == [{"evidence_identifier": "EV-1", "title": "Complaint", "source_reference": "TW-1", "temporal": None}]


def test_advisory_is_non_authoritative_and_requires_human_review():
    result = advisory(
        workflow="INVESTIGATION_SYNTHESIS",
        deterministic_result={"status": "CONTROLLED"},
        grounded_context={"policy_version": "v1", "tenant_scope_enforced": True},
        provider=_Provider(),
    )
    assert result["status"] == "PROVIDER_COMPLETED"
    assert result["authoritative"] is False
    assert result["human_review_required"] is True
    assert result["causality_state"] == "NOT_ESTABLISHED"
