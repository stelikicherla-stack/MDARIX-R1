"""Safe audit event construction using the existing AuditEvent model."""
from __future__ import annotations
from typing import Any
from datetime import datetime, timezone, timedelta
from backend.app.db.models.foundation import AuditEvent

SECRET_TERMS = ("password", "token", "secret", "credential", "api_key", "authorization")
def change_diff(before: dict[str, Any] | None, after: dict[str, Any] | None) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return only changed, redacted fields for a consistent audit diff."""
    old = before or {}; new = after or {}
    keys = set(old) | set(new)
    changed = {key for key in keys if old.get(key) != new.get(key)}
    return safe_details({key: old.get(key) for key in changed}), safe_details({key: new.get(key) for key in changed})
def safe_details(details: dict[str, Any] | None) -> dict[str, Any]:
    if not details: return {}
    return {key: value for key, value in details.items() if not any(term in key.lower() for term in SECRET_TERMS)}

def make_audit_event(*, tenant_id, actor_ref, action: str, entity_type: str, entity_id=None, correlation_id: str | None = None, details: dict[str, Any] | None = None, created_at=None, request=None, reason: str | None = None, old_values: dict[str, Any] | None = None, new_values: dict[str, Any] | None = None) -> AuditEvent:
    now = created_at or datetime.now(timezone.utc)
    source_ip = user_agent = None
    if request is not None:
        source_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
    return AuditEvent(id=None, tenant_id=tenant_id, actor_ref=actor_ref, action=action, entity_type=entity_type, entity_id=entity_id, correlation_id=correlation_id, details=safe_details(details), source_ip=source_ip, user_agent=user_agent, reason=reason, old_values=safe_details(old_values), new_values=safe_details(new_values), retention_until=now + timedelta(days=365 * 7), created_at=now)
