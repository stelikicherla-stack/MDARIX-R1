from pathlib import Path


def test_audit_immutability_migration_is_append_only():
    migration = Path("infrastructure/database/migrations/versions/o31audit_immutability.py").read_text(encoding="utf-8")
    assert "BEFORE UPDATE OR DELETE ON audit_events" in migration
    assert "audit_events are immutable" in migration


def test_existing_audit_framework_has_object_context_fields():
    model = Path("backend/app/db/models/foundation.py").read_text(encoding="utf-8")
    for field in ("entity_type", "entity_id", "tenant_id", "actor_ref", "action", "details"):
        assert field in model
