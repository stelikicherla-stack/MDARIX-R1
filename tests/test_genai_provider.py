import pytest
from genai.provider import GenAIProvider, GenAIUnavailable, redact_context

def test_genai_defaults_fail_safe_without_provider(monkeypatch):
    monkeypatch.delenv("MDARIX_GENAI_BASE_URL", raising=False)
    monkeypatch.delenv("MDARIX_GENAI_API_KEY", raising=False)
    result = GenAIProvider().complete("Explain this", {"token": "secret", "status": "open"})
    assert result.provider == "controlled"
    assert result.output["human_review_required"] is True
    assert result.output["causality_state"] == "NOT_ESTABLISHED"

def test_context_redaction_and_input_limit():
    assert redact_context({"password": "x", "status": "open"}) == {"password": "[REDACTED]", "status": "open"}
    with pytest.raises(GenAIUnavailable, match="TOKEN_LIMIT"):
        GenAIProvider(max_input_tokens=1).complete("a very long prompt", {})

def test_provider_outage_is_bounded(monkeypatch):
    monkeypatch.setenv("MDARIX_GENAI_BASE_URL", "http://127.0.0.1:1")
    monkeypatch.setenv("MDARIX_GENAI_API_KEY", "test")
    with pytest.raises(GenAIUnavailable, match="PROVIDER_UNAVAILABLE"):
        GenAIProvider(timeout_seconds=1, max_retries=0).complete("hello", {})
