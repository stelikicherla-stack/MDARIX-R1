from backend.app.controlled_export import prepare_export
from backend.app.retention import evaluate_disposition, record_disposition_result

def test_hold_blocks_expired_record():
    result = evaluate_disposition(tenant_id="a", record_tenant_id="a", retention_expired=True, active_hold=True, authorized=True)
    assert result.status == "BLOCKED" and result.reason == "ACTIVE_HOLD"

def test_disposition_requires_authorization_and_tenant_match():
    assert evaluate_disposition(tenant_id="a", record_tenant_id="b", retention_expired=True, active_hold=False, authorized=True).status == "DENIED"
    assert evaluate_disposition(tenant_id="a", record_tenant_id="a", retention_expired=True, active_hold=False, authorized=False).status == "DENIED"

def test_failed_disposition_is_not_reported_successfully():
    eligible = evaluate_disposition(tenant_id="a", record_tenant_id="a", retention_expired=True, active_hold=False, authorized=True)
    assert record_disposition_result(eligible, execution_succeeded=False).status == "FAILED"

def test_export_filters_secrets_and_hidden_fields():
    rows, decision = prepare_export([{ "identifier": "I-1", "status": "open", "password": "x", "hidden": "y" }], tenant_id="a", record_tenant_ids=["a"], authorized_fields={"identifier", "status"}, authorized=True)
    assert rows == [{"identifier": "I-1", "status": "open"}]
    assert set(decision.omitted_fields) == {"hidden", "password"}

def test_export_denies_cross_tenant_and_oversized_scope():
    assert prepare_export([{"identifier": "I-1"}], tenant_id="a", record_tenant_ids=["b"], authorized_fields={"identifier"}, authorized=True)[1].status == "DENIED"
    assert prepare_export([{"identifier": "I-1"}], tenant_id="a", record_tenant_ids=["a"], authorized_fields={"identifier"}, authorized=True, max_records=0)[1].status == "BLOCKED"
