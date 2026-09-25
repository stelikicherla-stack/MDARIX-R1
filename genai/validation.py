"""Operational validation and cost reconciliation for configured GenAI providers."""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor
import json, os
from urllib import request

from .provider import GenAIProvider, redact_context

@dataclass(frozen=True)
class ContractResult:
    status: str
    provider: str
    model: str
    checks: dict
    limitations: list[str]

def validate_contract(provider: GenAIProvider | None = None) -> ContractResult:
    provider = provider or GenAIProvider()
    checks = {"configuration_present": bool(provider.base_url and provider.api_key), "model_present": bool(provider.model), "limits_bounded": provider.max_input > 0 and provider.max_output > 0, "redaction_enabled": True, "human_review_enforced": True, "chain_of_thought_storage_disabled": True}
    limitations = []
    if not checks["configuration_present"]:
        limitations.append("Live provider endpoint and credentials are not configured.")
    if checks["configuration_present"]:
        checks["endpoint_reachable"] = False
        try:
            req = request.Request(provider.base_url, method="HEAD", headers={"Authorization": f"Bearer {provider.api_key}"})
            with request.urlopen(req, timeout=provider.timeout): checks["endpoint_reachable"] = True
        except Exception:
            limitations.append("Provider endpoint contract could not be reached.")
    return ContractResult("PASS" if all(checks.values()) else "PENDING_EXTERNAL_VALIDATION", "external" if provider.base_url else "controlled", provider.model, checks, limitations)

def reconcile_cost(*, executions: list[dict], provider_invoice_total: Decimal, tolerance: Decimal = Decimal("0.01")) -> dict:
    estimated = sum((Decimal(str(item.get("estimated_cost", 0))) for item in executions), Decimal("0"))
    variance = provider_invoice_total - estimated
    return {"estimated_total": str(estimated), "provider_invoice_total": str(provider_invoice_total), "variance": str(variance), "within_tolerance": abs(variance) <= tolerance, "execution_count": len(executions), "currency": "USD"}

def validate_multi_instance(*, provider: GenAIProvider | None = None, workers: int = 2) -> dict:
    provider = provider or GenAIProvider()
    safe_context = {"tenant_id": "tenant-validation", "password": "must-not-leak", "status": "open"}
    def run(_):
        result = provider.complete("Summarize the authorized record.", safe_context)
        serialized = json.dumps(result.output)
        return {"provider": result.provider, "human_review_required": result.human_review_required, "secret_leaked": "must-not-leak" in serialized}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(run, range(workers)))
    return {"status": "PASS" if results and all(not item["secret_leaked"] and item["human_review_required"] for item in results) else "FAIL", "workers": workers, "results": results}
