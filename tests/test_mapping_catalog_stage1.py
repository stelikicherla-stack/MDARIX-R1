from fastapi.testclient import TestClient
from backend.app.main import app
from pathlib import Path

def test_mapping_catalog_routes_are_registered():
    paths = set(app.openapi()["paths"])
    assert "/api/v1/admin/mapping/applications" in paths
    assert "/api/v1/admin/mapping/canonical/entities" in paths
    assert "/api/v1/admin/mapping/objects/{source_object_id}/fields" in paths
    assert "/api/v1/admin/mapping/connector-versions" in paths
    assert "/api/v1/admin/mapping/initial-mappings" in paths
    assert "/api/v1/admin/mapping/schema-drift" in paths
    assert "/api/v1/admin/mapping/dry-run" in paths
    assert "/api/v1/admin/mapping/validate" in paths
    assert "/api/v1/admin/mapping/schema-discovery" in paths
    assert "/api/v1/admin/mapping/compare" in paths
    assert "/api/v1/admin/configuration/connectors/{configuration_id}/provider-health" in paths
    assert "/api/v1/admin/configuration/connectors/{configuration_id}/discover-schema" in paths

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

def test_stage3_validation_blocks_duplicate_protected_and_circular_rules():
    from backend.app.mapping_catalog_router import validate_mapping, ValidationRequest
    result = validate_mapping(ValidationRequest(entity_id="Complaint", rules=[
        {"source": "a", "target": "external_id", "transform": "DIRECT"},
        {"source": "b", "target": "external_id", "transform": "DIRECT"},
        {"source": "c", "target": "status", "transform": "DIRECT", "reference_entity": "Complaint"},
        {"source": "d", "target": "tenant_id", "transform": "DIRECT"},
    ]), _admin_db(), _ctx())
    codes = {item["code"] for item in result["errors"]}
    assert result["status"] == "BLOCKED"
    assert {"DUPLICATE_TARGET", "PROTECTED_FIELD", "CIRCULAR_REFERENCE"} <= codes

def test_stage3_schema_discovery_reports_drift_without_activation():
    from backend.app.mapping_catalog_router import schema_discovery, DiscoveryRequest
    result = schema_discovery(DiscoveryRequest(source_object_id="TRACKWISE:COMPLAINT",
        baseline_fields=[{"name": "status", "data_type": "string", "required": False}],
        fields=[{"name": "status", "data_type": "integer", "required": True}, {"name": "new_field", "data_type": "string"}]), _admin_db(), _ctx())
    assert result["schema_status"] == "DRIFT_DETECTED"
    assert result["auto_applied"] is False
    assert {item["type"] for item in result["changes"]} == {"NEW_FIELD", "TYPE_CHANGED", "REQUIRED_NULLABLE_CHANGED"}

def test_stage3_suggestions_are_advisory_until_human_decision():
    from backend.app.mapping_catalog_router import suggestions, SuggestionRequest, suggestion_decision, SuggestionDecision
    result = suggestions(SuggestionRequest(source_fields=[{"field_name": "complaint_number"}], canonical_fields=[{"field_name": "complaint_number"}]), _admin_db(), _ctx())
    assert result["activation"] == "HUMAN_ACCEPTANCE_REQUIRED"
    assert result["suggestions"][0]["status"] == "AI_SUGGESTION_NOT_ACTIVE"
    decision = suggestion_decision(SuggestionDecision(suggestion_id=result["suggestions"][0]["suggestion_id"], decision="ACCEPT"), _admin_db(), _ctx())
    assert decision["active"] is False

def test_stage1_architecture_deliverables_exist():
    required = [
        "MAPPING_SOURCE_SYSTEM_ARCHITECTURE.md",
        "MAPPING_CANONICAL_DATA_MODEL.md",
        "MAPPING_SOURCE_FIELD_CATALOG.md",
        "MAPPING_TARGET_FIELD_CATALOG.md",
        "MAPPING_SOURCE_OF_TRUTH_POLICY.md",
        "MAPPING_INITIAL_FIELD_MATRIX.md",
        "MAPPING_STAGE1_REPORT.md",
    ]
    assert all((Path("docs") / name).exists() for name in required)
