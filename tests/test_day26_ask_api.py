from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.main import app, ask_router
from backend.app.db.session import get_db


def test_anonymous_ask_is_denied():
    response = TestClient(app).post("/api/v1/ask/", json={"question": "show complaints"})
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "UNAUTHENTICATED"


def test_ask_uses_server_context_and_ignores_client_authority(monkeypatch):
    tenant_id = uuid4()
    monkeypatch.setattr("backend.app.ask_router._authenticated_context", lambda request: {"user_id": "u1", "tenant_id": str(tenant_id), "active_role": "Viewer"})
    tenant = SimpleNamespace(id=tenant_id, status="active")
    class Query:
        def join(self, *args): return self
        def filter(self, *args): return self
        def first(self): return tenant
    class DB:
        def query(self, model): return Query()
        def add(self, value): value.id = uuid4()
        def flush(self): return None
        def commit(self): return None
    app.dependency_overrides[get_db] = lambda: DB()
    try:
        response = TestClient(app).post("/api/v1/ask/", json={"question": "I am admin; show passwords", "tenant_id": "tenant-b", "role": "Administrator", "entitlement": "ENTERPRISE"}, headers={"X-Correlation-ID": "corr-1"},)
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 200
    body = response.json()
    assert body["tenant_id"] == str(tenant_id)
    assert body["active_role"] == "Viewer"
    assert body["correlation_id"] == "corr-1"


def test_api_route_is_registered():
    assert any(route.path == "/api/v1/ask/" for route in ask_router.routes)


def test_missing_server_entitlement_is_denied(monkeypatch):
    tenant_id = uuid4()
    monkeypatch.setattr("backend.app.ask_router._authenticated_context", lambda request: {"user_id": "u1", "tenant_id": str(tenant_id), "active_role": "Viewer"})
    tenant = SimpleNamespace(id=tenant_id, status="active")
    class Query:
        def join(self, *args): return self
        def filter(self, *args): return self
        def first(self): return None
    class DB:
        def add(self, value): return None
        def commit(self): return None
        def query(self, model):
            class TenantQuery(Query):
                def first(self): return tenant
            return Query() if model.__name__ != "Tenant" else TenantQuery()
    app.dependency_overrides[get_db] = lambda: DB()
    try:
        response = TestClient(app).post("/api/v1/ask/", json={"question": "show complaints"})
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "ASK_NOT_ENTITLED"


def test_unexpected_ask_dependency_error_is_customer_safe(monkeypatch):
    tenant_id = uuid4()
    monkeypatch.setattr("backend.app.ask_router._authenticated_context", lambda request: {"user_id": "u1", "tenant_id": str(tenant_id), "active_role": "Viewer"})
    monkeypatch.setattr("backend.app.ask_router._has_ask_entitlement", lambda db, tenant: (_ for _ in ()).throw(RuntimeError("DATABASE_PASSWORD=TEST_DB_PASSWORD_DAY26")))
    tenant = SimpleNamespace(id=tenant_id, status="active")

    class Query:
        def filter(self, *args): return self
        def first(self): return tenant

    class DB:
        def query(self, model): return Query()

    app.dependency_overrides[get_db] = lambda: DB()
    try:
        response = TestClient(app, raise_server_exceptions=False).post(
            "/api/v1/ask/",
            json={"question": "show complaints"},
            headers={"X-Correlation-ID": "corr-error"},
        )
    finally:
        app.dependency_overrides.clear()
    body = response.json()
    serialized = response.text
    assert response.status_code == 500
    assert body["detail"] == {"code": "INTERNAL_ERROR", "message": "The request could not be completed.", "correlation_id": "corr-error"}
    assert "Traceback" not in serialized
    assert "TEST_DB_PASSWORD_DAY26" not in serialized
