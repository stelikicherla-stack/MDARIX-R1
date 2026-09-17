from integration.gateway import ConnectorRun, detect_schema_drift, source_record_fingerprint

def record(version="1"):
    return {"source_record_id":"C-1", "source_record_version":version, "identifier":"C-1"}

def test_retry_same_source_record_is_idempotent():
    run = ConnectorRun("tenant-a", "conn-1", "run-1")
    result = run.ingest([record(), record()], source_system="QMS", required_fields={"identifier"})
    assert result["accepted"] == [record()] and result["duplicates"] == 1 and result["state"] == "HEALTHY"

def test_source_version_change_is_a_new_controlled_record():
    run = ConnectorRun("tenant-a", "conn-1", "run-1")
    result = run.ingest([record("1"), record("2")], source_system="QMS", required_fields={"identifier"})
    assert result["processed"] == 2 and result["duplicates"] == 0 and result["status"] == "COMPLETE"

def test_missing_required_field_is_visible_partial_failure():
    run = ConnectorRun("tenant-a", "conn-1", "run-1")
    result = run.ingest([record(), {"source_record_id":"C-2"}], source_system="QMS", required_fields={"identifier"})
    assert result["status"] == "PARTIAL" and result["state"] == "DEGRADED"

def test_schema_drift_and_fingerprint_are_deterministic():
    assert detect_schema_drift({"id", "status"}, {"id", "label"}) == {"status":"DRIFT", "missing":["status"], "added":["label"]}
    assert source_record_fingerprint("a", "qms", "1", "v1", {"x":1}) == source_record_fingerprint("a", "qms", "1", "v1", {"x":1})
