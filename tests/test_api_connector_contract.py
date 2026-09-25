import json

import pytest

from integration.api_contract import compare_schema, fetch_page, idempotency_key, normalize_failure, schema_fingerprint


def test_contract_paginates_with_cursor_and_preserves_incremental_filter():
    calls = []
    pages = {
        None: {"records": [{"id": "1"}], "next_cursor": "c1"},
        "c1": {"records": [{"id": "2"}], "next_cursor": None},
    }

    def request(url, headers, timeout):
        calls.append(url)
        cursor = "c1" if "cursor=c1" in url else None
        return 200, {}, json.dumps(pages[cursor]).encode()

    from integration.api_contract import iter_pages
    result = list(iter_pages("http://provider.test/api", "records/Complaint", limit=25, since="2026-01-01", request_fn=request))
    assert [item["records"][0]["id"] for item in result] == ["1", "2"]
    assert "since=2026-01-01" in calls[0]
    assert "cursor=c1" in calls[1]


def test_contract_retries_retryable_failure_and_reports_attempts(monkeypatch):
    attempts = []

    def request(url, headers, timeout):
        attempts.append(1)
        if len(attempts) < 3:
            from urllib.error import URLError
            raise URLError("offline")
        return 200, {}, b'{"records": []}'

    monkeypatch.setattr("integration.api_contract.time.sleep", lambda _: None)
    result = fetch_page("http://provider.test", "health", request_fn=request, max_attempts=3)
    assert len(attempts) == 3
    assert result["_contract"]["attempts"] == 3


def test_contract_normalizes_auth_and_rate_limit_errors():
    from urllib.error import HTTPError
    from email.message import Message
    headers = Message(); headers["Retry-After"] = "2"
    failure = normalize_failure(HTTPError("http://provider.test", 429, "rate", headers, None))
    assert failure.category == "RATE_LIMIT"
    assert failure.retryable is True
    assert failure.retry_after_seconds == 2


def test_schema_drift_and_idempotency_are_deterministic():
    result = compare_schema(["id", "status"], ["id", "label"])
    assert result["status"] == "DRIFT"
    assert result["missing"] == ["status"]
    assert result["added"] == ["label"]
    assert schema_fingerprint(["b", "a"]) == schema_fingerprint(["a", "b"])
    assert idempotency_key("tenant-a", "trackwise", "Complaint", {"external_id": "C-1", "status": "open"}) == idempotency_key("tenant-a", "trackwise", "Complaint", {"status": "open", "external_id": "C-1"})


def test_contract_does_not_retry_non_retryable_provider_error(monkeypatch):
    def request(url, headers, timeout):
        from urllib.error import HTTPError
        raise HTTPError(url, 401, "unauthorized", {}, None)
    monkeypatch.setattr("integration.api_contract.time.sleep", lambda _: pytest.fail("must not sleep"))
    with pytest.raises(RuntimeError, match="HTTP_401"):
        fetch_page("http://provider.test", "records", request_fn=request, max_attempts=3)
