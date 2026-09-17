"""Fail-closed retention and disposition decision rules."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class DispositionDecision:
    status: str
    reason: str
    audit_required: bool = True

def evaluate_disposition(*, tenant_id: str, record_tenant_id: str | None, retention_expired: bool, active_hold: bool, authorized: bool, now: datetime | None = None) -> DispositionDecision:
    if not tenant_id or record_tenant_id != tenant_id:
        return DispositionDecision("DENIED", "TENANT_CONTEXT_MISMATCH")
    if not authorized:
        return DispositionDecision("DENIED", "AUTHORIZATION_REQUIRED")
    if not retention_expired:
        return DispositionDecision("NOT_ELIGIBLE", "RETENTION_PERIOD_NOT_REACHED")
    if active_hold:
        return DispositionDecision("BLOCKED", "ACTIVE_HOLD")
    return DispositionDecision("ELIGIBLE_FOR_REVIEW", "RETENTION_PERIOD_REACHED")

def record_disposition_result(decision: DispositionDecision, *, execution_succeeded: bool) -> DispositionDecision:
    if decision.status != "ELIGIBLE_FOR_REVIEW":
        return decision
    return DispositionDecision("DISPOSED" if execution_succeeded else "FAILED", "CONTROLLED_DISPOSITION_COMPLETED" if execution_succeeded else "CONTROLLED_DISPOSITION_FAILED")
