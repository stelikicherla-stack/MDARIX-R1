import json
import pytest
import genai.provider as provider_module
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


def test_groq_mode_uses_chat_completions_contract(monkeypatch):
    captured = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps({
                "choices": [{"message": {"content": "Evidence requires human review."}}],
                "usage": {"prompt_tokens": 12, "completion_tokens": 7},
            }).encode()

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["body"] = json.loads(request.data)
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setenv("MDARIX_GENAI_PROVIDER", "groq")
    monkeypatch.setenv("MDARIX_GENAI_API_KEY", "test-key")
    monkeypatch.setenv("MDARIX_GENAI_MODEL", "llama-3.3-70b-versatile")
    monkeypatch.setattr(provider_module.request, "urlopen", fake_urlopen)

    result = provider_module.GenAIProvider(max_retries=0).complete("Summarize the evidence", {"status": "open"})

    assert captured["url"] == provider_module.GROQ_BASE_URL
    assert captured["body"]["messages"][0]["role"] == "user"
    assert captured["body"]["temperature"] == 0
    assert captured["timeout"] == 20
    assert result.provider == "groq"
    assert result.output["answer"] == "Evidence requires human review."
    assert result.human_review_required is True
