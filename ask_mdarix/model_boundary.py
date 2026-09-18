from dataclasses import dataclass
from typing import Any, Mapping

from backend.app.ai_boundary import AIBoundaryDecision, build_context


@dataclass(frozen=True)
class ModelBoundaryResult:
    status: str
    context: tuple[dict[str, Any], ...]
    decisions: tuple[AIBoundaryDecision, ...]
    response: dict[str, Any]


def build_model_context(records: list[Mapping[str, Any]], *, tenant_id: str, authorized_fields: set[str]) -> ModelBoundaryResult:
    safe: list[dict[str, Any]] = []
    decisions: list[AIBoundaryDecision] = []
    for record in records:
        context, decision = build_context(record, authorized_fields=authorized_fields, tenant_id=tenant_id, record_tenant_id=record.get("tenant_id"))
        decisions.append(decision)
        if decision.allowed:
            safe.append(context)
    return ModelBoundaryResult("READY", tuple(safe), tuple(decisions), {"type": "CONTROLLED_CONTEXT", "model_invocation": "NOT_IMPLEMENTED"})


def dependency_failure(code: str = "AI_UNAVAILABLE") -> dict[str, str]:
    return {"status": "DEPENDENCY_UNAVAILABLE", "code": code, "message": "The investigation dependency is unavailable."}
