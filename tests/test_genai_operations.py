from decimal import Decimal
from genai.provider import GenAIProvider
from genai.validation import reconcile_cost, validate_contract, validate_multi_instance

def test_contract_validation_is_explicit_when_unconfigured(monkeypatch):
    monkeypatch.delenv("MDARIX_GENAI_BASE_URL", raising=False)
    monkeypatch.delenv("MDARIX_GENAI_API_KEY", raising=False)
    result = validate_contract(GenAIProvider())
    assert result.status == "PENDING_EXTERNAL_VALIDATION"
    assert result.checks["redaction_enabled"] and result.checks["chain_of_thought_storage_disabled"]

def test_cost_reconciliation_reports_variance():
    result = reconcile_cost(executions=[{"estimated_cost": "0.10"}, {"estimated_cost": "0.20"}], provider_invoice_total=Decimal("0.30"))
    assert result["within_tolerance"] and result["estimated_total"] == "0.30"

def test_concurrent_validation_is_secret_safe(monkeypatch):
    monkeypatch.delenv("MDARIX_GENAI_BASE_URL", raising=False)
    monkeypatch.delenv("MDARIX_GENAI_API_KEY", raising=False)
    result = validate_multi_instance(provider=GenAIProvider(), workers=3)
    assert result["status"] == "PASS" and len(result["results"]) == 3
