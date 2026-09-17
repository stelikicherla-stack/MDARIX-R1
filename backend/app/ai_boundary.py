"""Fail-closed, server-side allowlist for AI context construction."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping

AI_ALLOWED_FIELDS = frozenset({"id", "identifier", "title", "description", "status", "type", "category", "product_id", "product_version_id", "investigation_id", "event_time", "effective_time", "recorded_time", "source_reference", "provenance", "limitations", "observations", "hypotheses", "evidence_references"})
AI_RESTRICTED_FIELDS = frozenset({"email", "phone", "address", "display_name", "organization"})
AI_PROHIBITED_FIELDS = frozenset({"password", "password_hash", "verification_token", "reset_token", "session_token", "smtp_password", "api_key", "api_secret", "connector_secret", "private_key", "encryption_key", "database_password", "secret", "token"})

@dataclass(frozen=True)
class AIBoundaryDecision:
    allowed: bool
    policy_version: str
    included_fields: tuple[str, ...]
    omitted_fields: tuple[str, ...]
    reason: str

def _classification(field: str) -> str:
    lowered = field.lower()
    if field in AI_PROHIBITED_FIELDS or any(value in lowered for value in ("password", "secret", "token", "credential", "private_key")):
        return "PROHIBITED"
    if field in AI_RESTRICTED_FIELDS or field not in AI_ALLOWED_FIELDS:
        return "RESTRICTED"
    return "ALLOWED"

def build_context(record: Mapping[str, Any], *, authorized_fields: set[str], tenant_id: str, record_tenant_id: str | None, policy_version: str = "R1-AI-DATA-BOUNDARY-v1") -> tuple[dict[str, Any], AIBoundaryDecision]:
    """Build context only after the caller has performed server authorization."""
    if not tenant_id or record_tenant_id != tenant_id:
        return {}, AIBoundaryDecision(False, policy_version, (), tuple(record.keys()), "TENANT_CONTEXT_MISMATCH")
    included: dict[str, Any] = {}
    omitted: list[str] = []
    for field, value in record.items():
        if field not in authorized_fields or _classification(field) != "ALLOWED":
            omitted.append(field)
        else:
            included[field] = value
    return included, AIBoundaryDecision(True, policy_version, tuple(sorted(included)), tuple(sorted(omitted)), "AUTHORIZED_CONTEXT")
