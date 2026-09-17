"""Tenant-, field-, and size-bounded export preparation."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping
from backend.app.ai_boundary import AI_PROHIBITED_FIELDS

@dataclass(frozen=True)
class ExportDecision:
    status: str
    reason: str
    record_count: int
    omitted_fields: tuple[str, ...] = ()

def prepare_export(records: list[Mapping[str, Any]], *, tenant_id: str, record_tenant_ids: list[str | None], authorized_fields: set[str], authorized: bool, max_records: int = 1000) -> tuple[list[dict[str, Any]], ExportDecision]:
    if not authorized:
        return [], ExportDecision("DENIED", "AUTHORIZATION_REQUIRED", 0)
    if len(records) > max_records:
        return [], ExportDecision("BLOCKED", "OPERATING_LIMIT_EXCEEDED", 0)
    if any(not tenant_id or record_tenant != tenant_id for record_tenant in record_tenant_ids):
        return [], ExportDecision("DENIED", "TENANT_CONTEXT_MISMATCH", 0)
    output: list[dict[str, Any]] = []
    omitted: set[str] = set()
    for record in records:
        safe: dict[str, Any] = {}
        for field, value in record.items():
            if field not in authorized_fields or field in AI_PROHIBITED_FIELDS or any(secret in field.lower() for secret in ("password", "secret", "token", "credential")):
                omitted.add(field)
            else:
                safe[field] = value
        output.append(safe)
    return output, ExportDecision("READY", "AUTHORIZED_FILTERED_EXPORT", len(output), tuple(sorted(omitted)))
