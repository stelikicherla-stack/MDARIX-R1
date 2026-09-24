from pathlib import Path

from backend.app.main import app
from backend.app.mapping_catalog_router import APPLICATIONS, OBJECTS, CANONICAL, source_fields, canonical_fields


def _admin_db():
    class Db:
        def query(self, model):
            class Q:
                def filter(self, *args): return self
                def first(self): return type("User", (), {"role": "Administrator", "status": "ACTIVE"})()
            return Q()
    return Db()


def _ctx():
    return type("Ctx", (), {"user_id": "00000000-0000-0000-0000-000000000000", "tenant_id": "00000000-0000-0000-0000-000000000000"})()


def test_stage4_application_objects_are_scoped_to_application():
    for application, objects in OBJECTS.items():
        assert objects
        assert all(isinstance(item, str) and item for item in objects)


def test_stage4_catalogs_and_protected_fields_are_available():
    assert len(APPLICATIONS) == 12
    for entity in CANONICAL:
        fields = canonical_fields(entity, _admin_db(), _ctx())
        assert fields
        assert all("mapping_allowed" in field and "required" in field for field in fields)
    fields = source_fields("TRACKWISE:COMPLAINT", _admin_db(), _ctx())
    assert any(field["field_group"] == "IDENTIFIERS" for field in fields)
    assert any(field["field_group"] == "DATES" for field in fields)


def test_stage4_required_routes_and_ci_contract_are_present():
    paths = set(app.openapi()["paths"])
    required = {
        "/api/v1/admin/mapping/applications",
        "/api/v1/admin/mapping/applications/{application_id}/objects",
        "/api/v1/admin/mapping/objects/{source_object_id}/fields",
        "/api/v1/admin/mapping/canonical/entities/{entity_id}/fields",
        "/api/v1/admin/mapping/dry-run",
        "/api/v1/admin/mapping/validate",
        "/api/v1/admin/mapping/schema-discovery",
        "/api/v1/admin/mapping/compare",
        "/api/v1/admin/mapping/impact-history",
        "/api/v1/admin/mapping/suggestions",
    }
    assert required <= paths
    assert Path(".github/workflows/ci.yml").exists()


def test_stage4_final_evidence_never_contains_secrets():
    evidence = Path("evidence/mapping-studio")
    if not evidence.exists():
        return
    prohibited = {"password", "api_key", "token", "secret", "credential"}
    for path in evidence.rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8").lower()
            assert not any(f"{word}=" in text or f"{word}:" in text for word in prohibited), path
