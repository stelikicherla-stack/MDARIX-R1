"""Tenant-safe context construction and optional GenAI advisory augmentation."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from genai.provider import GenAIProvider, GenAIUnavailable
from investigation_workspace.schemas import InvestigationWorkspaceRequest
from investigation_workspace.service import InvestigationWorkspaceService


CONTEXT_POLICY_VERSION = "R1-GROUNDED-AI-CONTEXT-v1"
ALLOWED_KEYS = frozenset({
    "id", "investigation_identifier", "investigation_question", "status", "opened_at", "closed_at",
    "product_id", "product_version_id", "product", "selected_version", "overview", "configuration",
    "changes", "manufacturing", "complaints", "risks", "controls", "provenance", "limitations",
    "mode", "as_of", "event_time_distinct_from_known_time", "late_arriving_evidence_count",
    "evidence_identifier", "evidence_type", "title", "source_reference", "reliability_status", "fact_type",
    "temporal", "effective_timestamp", "recorded_timestamp", "ingestion_timestamp", "chunks", "chunk_id",
    "sequence_number", "source_anchor", "excerpt", "materialized", "observations", "observation_id",
    "statement", "observation_type", "extraction_method", "quality_status", "entity_links", "entity_type",
    "entity_id", "raw_reference", "resolution_status", "nodes", "relationships", "metadata", "warning",
    "relationship_semantics", "unknowns", "missing_evidence", "contradictions", "hypotheses",
})
PROHIBITED_FRAGMENTS = ("password", "secret", "token", "credential", "cookie", "authorization", "api_key")


def _filter(value: Any) -> Any:
    if isinstance(value, list):
        return [_filter(item) for item in value[:25]]
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            lowered = str(key).lower()
            if any(fragment in lowered for fragment in PROHIBITED_FRAGMENTS):
                continue
            if key in ALLOWED_KEYS:
                result[key] = _filter(item)
        return result
    return value[:1000] if isinstance(value, str) else value


def source_provenance(context: dict[str, Any]) -> list[dict[str, Any]]:
    """Return citation metadata without copying evidence text into API metadata."""
    return [
        {
            "evidence_identifier": item.get("evidence_identifier"),
            "title": item.get("title"),
            "source_reference": item.get("source_reference"),
            "temporal": item.get("temporal"),
        }
        for item in context.get("evidence_context", [])
    ]


def build_authorized_context(
    db: Session,
    *,
    tenant_id: UUID,
    investigation_id: UUID,
    product_version_id: UUID | None = None,
    temporal_mode: str = "current",
    as_of: datetime | None = None,
) -> dict[str, Any]:
    """Build context from tenant-scoped services; request-supplied tenant identity is never accepted."""
    workspace = InvestigationWorkspaceService().workspace(
        db,
        InvestigationWorkspaceRequest(
            tenant_id=tenant_id,
            investigation_id=investigation_id,
            product_version_id=product_version_id,
            temporal_mode=temporal_mode.lower(),
            as_of=as_of,
            include_retrieval=False,
        ),
    )
    raw = workspace.model_dump(mode="json")
    return {
        "policy_version": CONTEXT_POLICY_VERSION,
        "tenant_scope_enforced": True,
        "field_policy": "SERVER_ALLOWLIST_FAIL_CLOSED",
        "investigation": _filter(raw.get("investigation", {})),
        "product_context": _filter(raw.get("product_context", {})),
        "temporal_context": _filter(raw.get("temporal_context", {})),
        "evidence_context": _filter(raw.get("evidence_context", [])),
        "relationship_context": _filter(raw.get("relationship_context", {})),
        "limitations": _filter(raw.get("limitations", [])),
    }


def advisory(
    *,
    workflow: str,
    deterministic_result: Any,
    grounded_context: dict[str, Any],
    question: str | None = None,
    provider: GenAIProvider | None = None,
) -> dict[str, Any]:
    """Return a clearly separated advisory; deterministic output remains authoritative."""
    client = provider or GenAIProvider()
    prompt = (
        f"Workflow: {workflow}. Review the authorized context and controlled result. "
        "Return concise advisory observations, contradictions, unknowns, missing evidence, and next review questions. "
        "Do not claim causality or root cause, make a regulatory or human decision, modify records, or issue external actions. "
        f"User question: {question or 'None supplied'}."
    )
    try:
        result = client.complete(prompt, {"grounded_context": grounded_context, "controlled_result": deterministic_result})
        return {
            "status": "PROVIDER_COMPLETED",
            "provider_output": result.output,
            "provider": result.provider,
            "model": result.model,
            "model_version": result.model_version,
            "audit": client.audit_details(result),
            "context_policy_version": grounded_context.get("policy_version"),
            "human_review_required": True,
            "causality_state": "NOT_ESTABLISHED",
            "authoritative": False,
        }
    except GenAIUnavailable as exc:
        return {
            "status": "DETERMINISTIC_FALLBACK",
            "error_state": type(exc).__name__,
            "limitations": ["GenAI provider unavailable; controlled deterministic result retained."],
            "context_policy_version": grounded_context.get("policy_version"),
            "human_review_required": True,
            "causality_state": "NOT_ESTABLISHED",
            "authoritative": False,
        }
