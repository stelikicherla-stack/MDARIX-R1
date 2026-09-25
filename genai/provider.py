"""Bounded GenAI provider boundary.

No provider is contacted unless explicitly configured.  Responses are
structured and never retain hidden chain-of-thought; only a short rationale
summary is returned for human review.
"""
from __future__ import annotations
import json, os, re, time
from dataclasses import dataclass
from urllib import request

CONFIG_VERSION = "genai-config-1"
PROMPT_VERSION = "mdarix-safe-prompt-1"
GROQ_BASE_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_DEFAULT_MODEL = "llama-3.3-70b-versatile"
SENSITIVE = re.compile(r"(?i)(password|token|secret|cookie|authorization|api[_-]?key|credential)\s*[:=]\s*[^,;\n]+")

class GenAIUnavailable(RuntimeError): pass

@dataclass(frozen=True)
class GenAIResult:
    provider: str
    model: str
    model_version: str
    output: dict
    input_tokens: int
    output_tokens: int
    estimated_cost: float
    latency_ms: int
    human_review_required: bool = True

def redact_context(value):
    if isinstance(value, dict):
        return {k: "[REDACTED]" if re.search(r"(?i)(password|token|secret|cookie|authorization|api[_-]?key|credential)", str(k)) else redact_context(v) for k, v in value.items()}
    if isinstance(value, list): return [redact_context(v) for v in value]
    return SENSITIVE.sub(lambda m: m.group(1) + ": [REDACTED]", str(value)) if isinstance(value, str) else value

class GenAIProvider:
    def __init__(self, *, base_url=None, api_key=None, model=None, timeout_seconds=None, max_retries=None, max_input_tokens=None, max_output_tokens=None, cost_per_1k_tokens=None):
        self.provider_name = os.getenv("MDARIX_GENAI_PROVIDER", "controlled").strip().lower()
        configured_base_url = base_url or os.getenv("MDARIX_GENAI_BASE_URL")
        self.base_url = configured_base_url or (GROQ_BASE_URL if self.provider_name == "groq" else None)
        self.api_key = api_key or os.getenv("MDARIX_GENAI_API_KEY")
        default_model = GROQ_DEFAULT_MODEL if self.provider_name == "groq" else "mdarix-controlled"
        self.model = model or os.getenv("MDARIX_GENAI_MODEL", default_model)
        self.model_version = os.getenv("MDARIX_GENAI_MODEL_VERSION", "unconfigured")
        self.timeout = int(timeout_seconds or os.getenv("MDARIX_GENAI_TIMEOUT_SECONDS", "20"))
        self.retries = int(max_retries if max_retries is not None else os.getenv("MDARIX_GENAI_MAX_RETRIES", "2"))
        self.max_input = int(max_input_tokens or os.getenv("MDARIX_GENAI_MAX_INPUT_TOKENS", "4000"))
        self.max_output = int(max_output_tokens or os.getenv("MDARIX_GENAI_MAX_OUTPUT_TOKENS", "1000"))
        self.cost_per_1k = float(cost_per_1k_tokens or os.getenv("MDARIX_GENAI_COST_PER_1K_TOKENS", "0"))

    def health(self):
        return {"configured": bool(self.base_url and self.api_key), "provider": self.provider_name if self.base_url else "controlled", "model": self.model, "configuration_version": CONFIG_VERSION, "human_review_required": True, "hidden_chain_of_thought_persisted": False}

    @staticmethod
    def audit_details(result: GenAIResult) -> dict:
        """Safe metadata suitable for the enterprise AIExecution/audit tables."""
        return {"provider": result.provider, "model": result.model, "model_version": result.model_version,
                "input_tokens": result.input_tokens, "output_tokens": result.output_tokens,
                "estimated_cost": result.estimated_cost, "latency_ms": result.latency_ms,
                "human_review_required": True, "hidden_chain_of_thought_persisted": False}

    def complete(self, prompt: str, context: dict | None = None) -> GenAIResult:
        safe_prompt = SENSITIVE.sub(lambda m: m.group(1) + ": [REDACTED]", prompt)
        safe_context = redact_context(context or {})
        input_tokens = max(1, (len(safe_prompt) + len(json.dumps(safe_context, default=str))) // 4)
        if input_tokens > self.max_input: raise GenAIUnavailable("GENAI_INPUT_TOKEN_LIMIT")
        started = time.monotonic()
        if not self.base_url or not self.api_key:
            return GenAIResult("controlled", self.model, CONFIG_VERSION, {"status": "PROVIDER_NOT_CONFIGURED", "answer": None, "limitations": ["Live GenAI provider is not configured."], "human_review_required": True, "causality_state": "NOT_ESTABLISHED"}, input_tokens, 0, 0.0, int((time.monotonic()-started)*1000))
        if self.provider_name == "groq":
            payload = json.dumps({
                "model": self.model,
                "messages": [{"role": "user", "content": safe_prompt + "\n\nAuthorized context:\n" + json.dumps(safe_context, default=str)}],
                "max_tokens": self.max_output,
                "temperature": 0,
            }).encode()
        else:
            payload = json.dumps({"model": self.model, "prompt": safe_prompt, "context": safe_context, "max_tokens": self.max_output}).encode()
        error = None
        for attempt in range(self.retries + 1):
            try:
                req = request.Request(self.base_url, data=payload, headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"})
                with request.urlopen(req, timeout=self.timeout) as response: raw = json.loads(response.read())
                if self.provider_name == "groq":
                    answer = ((raw.get("choices") or [{}])[0].get("message") or {}).get("content")
                    usage = raw.get("usage") or {}
                    output_tokens = int(usage.get("completion_tokens") or max(1, len(str(answer or "")) // 4))
                    input_tokens = int(usage.get("prompt_tokens") or input_tokens)
                else:
                    answer = raw.get("answer", raw.get("output", raw.get("text")))
                    output_tokens = min(self.max_output, max(1, len(str(answer or "")) // 4))
                output = {"answer": answer, "limitations": ["Provider output requires human review."], "human_review_required": True, "causality_state": "NOT_ESTABLISHED"}
                return GenAIResult(self.provider_name if self.provider_name != "controlled" else "external", self.model, self.model_version, output, input_tokens, output_tokens, ((input_tokens+output_tokens)/1000)*self.cost_per_1k, int((time.monotonic()-started)*1000))
            except Exception as exc: error = exc; time.sleep(min(2 ** attempt, 4))
        raise GenAIUnavailable(f"GENAI_PROVIDER_UNAVAILABLE: {type(error).__name__}")
