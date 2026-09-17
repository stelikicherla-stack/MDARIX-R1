"""Safe audit event construction using the existing AuditEvent model."""
from __future__ import annotations
from typing import Any
from backend.app.db.models.foundation import AuditEvent

SECRET_TERMS = ("password", "token", "secret", "credential", "api_key", "authorization")
def safe_details(details: dict[str, Any] | None) -> dict[str, Any]:
    if not details: return {}
    return {key: value for key, value in details.items() if not any(term in key.lower() for term in SECRET_TERMS)}

def make_audit_event(*, tenant_id, actor_ref, action: str, entity_type: str, entity_id=None, correlation_id: str | None = None, details: dict[str, Any] | None = None, created_at=None) -> AuditEvent:
    from datetime import datetime, timezone
    return AuditEvent(id=None, tenant_id=tenant_id, actor_ref=actor_ref, action=action, entity_type=entity_type, entity_id=entity_id, correlation_id=correlation_id, details=safe_details(details), created_at=created_at or datetime.now(timezone.utc))
