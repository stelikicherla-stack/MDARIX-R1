from pathlib import Path


ROOT = Path(__file__).parents[1]
UI = (ROOT / "frontend" / "src" / "main.tsx").read_text(encoding="utf-8")
ROUTER = (ROOT / "backend" / "app" / "access_router.py").read_text(encoding="utf-8")


def test_admin_dashboard_loads_all_control_plane_domains():
    required_reads = [
        "/api/v1/admin/identity/users",
        "/api/v1/admin/identity/roles",
        "/api/v1/admin/identity/permission-sets",
        "/api/v1/admin/identity/memberships",
        "/api/v1/admin/identity/persona-assignments",
        "/api/v1/admin/governance/entitlements",
        "/api/v1/admin/configuration/connectors",
        "/api/v1/admin/configuration/mappings",
        "/api/v1/admin/governance/policies",
        "/api/v1/admin/audit-history",
    ]
    for endpoint in required_reads:
        assert endpoint in UI
        assert endpoint.removeprefix("/api/v1") in ROUTER


def test_admin_create_forms_cover_required_resources():
    required_create_endpoints = [
        "/api/v1/admin/identity/users",
        "/api/v1/admin/identity/roles",
        "/api/v1/admin/identity/permission-sets",
        "/api/v1/admin/identity/persona-assignments",
        "/api/v1/admin/configuration/connectors",
        "/api/v1/admin/configuration/mappings",
        "/api/v1/admin/governance/approval-authorities",
        "/api/v1/admin/governance/sod-policies",
    ]
    for endpoint in required_create_endpoints:
        assert endpoint in UI
        route = endpoint.removeprefix("/api/v1")
        assert f'@router.post("{route}")' in ROUTER


def test_admin_edit_workflow_covers_every_editable_resource():
    resources = [
        "users",
        "roles",
        "permission-sets",
        "persona-assignments",
        "connectors",
        "mappings",
        "approval-authorities",
        "sod-policies",
    ]
    for resource in resources:
        assert resource in UI
        assert f'"{resource}"' in ROUTER
    assert "/api/v1/admin/control-plane/" in UI
    assert '@router.patch("/admin/control-plane/{resource}/{resource_id}")' in ROUTER


def test_admin_ui_exposes_controlled_administration_and_audit_feedback():
    assert "Administrator control plane" in UI
    assert "Controlled administration" in UI
    assert "The change was recorded in audit history." in UI
    assert "Tenant-scoped administration" in UI
