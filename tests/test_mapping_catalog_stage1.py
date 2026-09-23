from fastapi.testclient import TestClient
from backend.app.main import app

def test_mapping_catalog_routes_are_registered():
    paths = set(app.openapi()["paths"])
    assert "/api/v1/admin/mapping/applications" in paths
    assert "/api/v1/admin/mapping/canonical/entities" in paths
    assert "/api/v1/admin/mapping/objects/{source_object_id}/fields" in paths
    assert "/api/v1/admin/mapping/connector-versions" in paths
    assert "/api/v1/admin/mapping/initial-mappings" in paths

def test_catalog_contract_protects_platform_fields():
    from backend.app.mapping_catalog_router import canonical_fields
    class Db:
        def query(self, model):
            class Q:
                def filter(self, *args): return self
                def first(self): return type("User", (), {"role":"Administrator"})()
            return Q()
    ctx=type("Ctx", (), {"user_id":"00000000-0000-0000-0000-000000000000","tenant_id":"00000000-0000-0000-0000-000000000000"})()
    fields=canonical_fields("Complaint", Db(), ctx)
    protected=next(item for item in fields if item["field_name"] == "external_id")
    assert protected["mapping_allowed"] is True
    assert all(item["field_name"] not in {"tenant_id", "audit_id", "provenance_id"} for item in fields)
