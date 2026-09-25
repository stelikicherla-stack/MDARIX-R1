import pytest
from fastapi import HTTPException
from starlette.requests import Request

from backend.app.request_context import get_request_context


class EmptyDb:
    def query(self, _model):
        return self

    def filter(self, *_args):
        return self

    def first(self):
        return None


def request_with_session(token="not-durable"):
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/protected",
            "headers": [(b"cookie", f"mdarix_session={token}".encode())],
            "query_string": b"",
        }
    )


@pytest.mark.parametrize("environment", ["staging", "production"])
def test_non_durable_session_is_rejected_outside_development(monkeypatch, environment):
    monkeypatch.setenv("MDARIX_ENV", environment)
    monkeypatch.delenv("MDARIX_ALLOW_LEGACY_AUTH_FALLBACK", raising=False)

    with pytest.raises(HTTPException) as error:
        get_request_context(request_with_session(), EmptyDb())

    assert error.value.status_code == 401
    assert error.value.detail["code"] == "UNAUTHENTICATED"


def test_legacy_fallback_requires_explicit_opt_in(monkeypatch):
    monkeypatch.setenv("MDARIX_ENV", "development")
    monkeypatch.delenv("MDARIX_ALLOW_LEGACY_AUTH_FALLBACK", raising=False)

    with pytest.raises(HTTPException) as error:
        get_request_context(request_with_session(), EmptyDb())

    assert error.value.status_code == 401
