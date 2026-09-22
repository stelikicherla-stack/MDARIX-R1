"""Small, provider-neutral GenAI boundary for local and live qualification."""
from dataclasses import dataclass
import json
import os
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class ModelResult:
    text: str
    provider: str
    model: str
    human_review_required: bool = True


class ModelProvider:
    def generate(self, prompt: str, *, tenant_id: str, evidence_refs: list[str]) -> ModelResult:
        raise NotImplementedError


class MockModelProvider(ModelProvider):
    def generate(self, prompt: str, *, tenant_id: str, evidence_refs: list[str]) -> ModelResult:
        return ModelResult("Controlled draft generated from authorized evidence; human review required.", "mock", "deterministic", True)


class OpenAICompatibleProvider(ModelProvider):
    """Optional live adapter; credentials are read only from the server environment."""
    def generate(self, prompt: str, *, tenant_id: str, evidence_refs: list[str]) -> ModelResult:
        endpoint = os.environ.get("MDARIX_MODEL_ENDPOINT")
        api_key = os.environ.get("MDARIX_MODEL_API_KEY")
        model = os.environ.get("MDARIX_MODEL", "")
        if not endpoint or not api_key or not model:
            raise RuntimeError("MODEL_PROVIDER_NOT_CONFIGURED")
        payload = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}], "metadata": {"tenant_id": tenant_id, "evidence_refs": evidence_refs}}).encode()
        request = Request(endpoint, data=payload, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, method="POST")
        with urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode())
        text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        return ModelResult(text, "openai-compatible", model, True)


def configured_provider() -> ModelProvider:
    return OpenAICompatibleProvider() if os.environ.get("MDARIX_MODEL_ENDPOINT") else MockModelProvider()
