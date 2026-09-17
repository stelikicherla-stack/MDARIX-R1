from backend.app.ai_boundary import build_context

def test_context_is_allowlisted_before_provider_boundary():
    context, decision = build_context({"identifier": "INV-001", "status": "open", "password": "never", "email": "hidden@example.com"}, authorized_fields={"identifier", "status", "password", "email"}, tenant_id="tenant-a", record_tenant_id="tenant-a")
    assert context == {"identifier": "INV-001", "status": "open"}
    assert set(decision.omitted_fields) == {"email", "password"}

def test_cross_tenant_context_fails_closed():
    context, decision = build_context({"identifier": "INV-001"}, authorized_fields={"identifier"}, tenant_id="tenant-a", record_tenant_id="tenant-b")
    assert context == {} and decision.allowed is False and decision.reason == "TENANT_CONTEXT_MISMATCH"

def test_prompt_claim_cannot_expand_authorized_fields():
    context, decision = build_context({"identifier": "INV-001", "hidden_field": "secret"}, authorized_fields={"identifier"}, tenant_id="tenant-a", record_tenant_id="tenant-a")
    assert context == {"identifier": "INV-001"} and "hidden_field" in decision.omitted_fields
