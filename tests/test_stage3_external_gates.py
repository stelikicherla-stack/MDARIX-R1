import json
from types import SimpleNamespace

from backend.app.access_router import _provider_get


class _Response:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, _limit):
        return json.dumps({"schema": "v1", "fields": [{"name": "id"}]}).encode()


def test_provider_adapter_uses_server_credential_reference_and_sanitizes_response(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["authorization"] = request.headers.get("Authorization")
        captured["timeout"] = timeout
        return _Response()

    monkeypatch.setenv("TEST_CONNECTOR_TOKEN", "do-not-return")
    monkeypatch.setattr("backend.app.access_router.urlopen", fake_urlopen)
    row = SimpleNamespace(id="connector-1", configuration={
        "endpoint": "https://provider.invalid/api",
        "health_path": "health",
        "credential_ref": "TEST_CONNECTOR_TOKEN",
        "timeout_seconds": 3,
    })
    result = _provider_get(row, "health_path")
    assert result["status"] == "HEALTHY"
    assert captured == {
        "url": "https://provider.invalid/api/health",
        "authorization": "Bearer do-not-return",
        "timeout": 3.0,
    }
    assert "do-not-return" not in json.dumps(result)


def test_provider_adapter_reports_unconfigured_and_unreachable_without_secrets(monkeypatch):
    row = SimpleNamespace(id="connector-2", configuration={})
    assert _provider_get(row, "health_path")["status"] == "NOT_CONFIGURED"

    def fail(*_args, **_kwargs):
        raise TimeoutError()

    monkeypatch.setattr("backend.app.access_router.urlopen", fail)
    row.configuration = {"endpoint": "https://provider.invalid/api", "health_path": "health"}
    result = _provider_get(row, "health_path")
    assert result == {"status": "FAILED", "reason": "PROVIDER_UNREACHABLE"}
