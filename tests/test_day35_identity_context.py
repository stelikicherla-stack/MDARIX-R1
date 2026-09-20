from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from backend.app import access_router


def request_with_cookie(token: str = "") -> Request:
    headers = [(b"cookie", f"mdarix_session={token}".encode())] if token else []
    return Request({"type": "http", "method": "GET", "path": "/api/v1/me/context", "headers": headers, "query_string": b""})


class FakeQuery:
    def __init__(self, row):
        self.row = row

    def filter(self, *args):
        return self

    def first(self):
        return self.row


class FakeDb:
    def __init__(self, user):
        self.user = user

    def query(self, model):
        return FakeQuery(self.user)


def active_user(tenant_id="tenant-a", role="Viewer"):
    return SimpleNamespace(
        id="user-a",
        tenant_id=tenant_id,
        username="user-a@example.invalid",
        display_name="User A",
        role=role,
        status="ACTIVE",
    )


def test_context_uses_authenticated_persisted_user(monkeypatch):
    monkeypatch.setattr(access_router.auth_service, "context", lambda token: {"user_id": "user-a", "tenant_id": "tenant-a"})

    result = access_router.context(request_with_cookie("session-a"), FakeDb(active_user()))

    assert result["user_id"] == "user-a"
    assert result["tenant_id"] == "tenant-a"
    assert result["active_role"] == "Viewer"
    assert result["email"] == "user-a@example.invalid"


def test_context_requires_authentication():
    with pytest.raises(HTTPException) as error:
        access_router.context(request_with_cookie(), FakeDb(active_user()))

    assert error.value.status_code == 401
    assert error.value.detail["code"] == "UNAUTHENTICATED"


def test_context_rejects_session_tenant_mismatch(monkeypatch):
    monkeypatch.setattr(access_router.auth_service, "context", lambda token: {"user_id": "user-a", "tenant_id": "tenant-b"})

    with pytest.raises(HTTPException) as error:
        access_router.context(request_with_cookie("session-a"), FakeDb(active_user("tenant-a")))

    assert error.value.status_code == 401
    assert error.value.detail["code"] == "UNAUTHENTICATED"


def test_active_role_rejects_unassigned_role(monkeypatch):
    monkeypatch.setattr(access_router.auth_service, "context", lambda token: {"user_id": "user-a", "tenant_id": "tenant-a"})

    with pytest.raises(HTTPException) as error:
        access_router.active_role(
            access_router.RoleSwitch(role="Administrator"),
            request_with_cookie("session-a"),
            FakeDb(active_user()),
        )

    assert error.value.status_code == 403
    assert error.value.detail["code"] == "ROLE_NOT_ASSIGNED"


def test_administrator_gate_rejects_viewer(monkeypatch):
    monkeypatch.setattr(access_router, "_authenticated_user", lambda request, db: active_user(role="Viewer"))
    with pytest.raises(HTTPException) as error:
        access_router._require_administrator(request_with_cookie("session-a"), FakeDb(active_user()))
    assert error.value.status_code == 403
    assert error.value.detail["code"] == "ADMINISTRATOR_REQUIRED"


def test_administrator_gate_accepts_administrator(monkeypatch):
    admin = active_user(role="Administrator")
    monkeypatch.setattr(access_router, "_authenticated_user", lambda request, db: admin)
    assert access_router._require_administrator(request_with_cookie("session-a"), FakeDb(admin)) is admin
