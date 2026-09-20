"""Deny-by-default entitlement evaluation, separate from authorization policy."""

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping


@dataclass(frozen=True)
class EntitlementDecision:
    feature: str
    entitled: bool
    reason: str
    limits: Mapping[str, object]


def evaluate_entitlement(*, feature: str, plan_active: bool, feature_enabled: bool, assignment_active: bool, effective_from: datetime | None = None, now: datetime | None = None, limits: Mapping[str, object] | None = None) -> EntitlementDecision:
    if not feature.strip():
        return EntitlementDecision(feature, False, "FEATURE_REQUIRED", {})
    current = now or datetime.now().astimezone()
    if not plan_active:
        return EntitlementDecision(feature, False, "PLAN_INACTIVE", {})
    if not assignment_active:
        return EntitlementDecision(feature, False, "ASSIGNMENT_INACTIVE", {})
    if effective_from is not None and effective_from > current:
        return EntitlementDecision(feature, False, "NOT_YET_EFFECTIVE", {})
    if not feature_enabled:
        return EntitlementDecision(feature, False, "FEATURE_DISABLED", {})
    return EntitlementDecision(feature, True, "ENTITLED", dict(limits or {}))
