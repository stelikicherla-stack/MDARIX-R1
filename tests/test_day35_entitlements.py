from datetime import datetime, timedelta, timezone

from access_control.entitlements import evaluate_entitlement


def test_entitlement_requires_all_security_and_plan_gates():
    denied = evaluate_entitlement(feature="ASK_MDARIX", plan_active=True, feature_enabled=True, assignment_active=False)
    assert denied.entitled is False
    assert denied.reason == "ASSIGNMENT_INACTIVE"


def test_entitlement_is_not_effective_before_start_time():
    now = datetime.now(timezone.utc)
    denied = evaluate_entitlement(feature="ASK_MDARIX", plan_active=True, feature_enabled=True, assignment_active=True, effective_from=now + timedelta(minutes=1), now=now)
    assert denied.entitled is False
    assert denied.reason == "NOT_YET_EFFECTIVE"


def test_entitlement_returns_limits_only_when_entitled():
    result = evaluate_entitlement(feature="EVIDENCE_INTELLIGENCE", plan_active=True, feature_enabled=True, assignment_active=True, limits={"max_records": 100})
    assert result.entitled is True
    assert result.reason == "ENTITLED"
    assert result.limits == {"max_records": 100}
