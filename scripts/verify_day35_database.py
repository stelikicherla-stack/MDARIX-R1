"""Read-only verification of Day 35 schema and fixture invariants."""
from sqlalchemy import inspect, text
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app.db.session import engine, SessionLocal

REQUIRED_TABLES = {
    "tenant_memberships", "persona_assignments", "role_definitions",
    "permission_set_definitions", "role_assignments", "role_permission_sets",
    "connector_configurations", "mapping_configurations",
}


def main() -> int:
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    missing = REQUIRED_TABLES - tables
    if missing:
        print("DAY35_SCHEMA = BLOCKED")
        print("Missing tables:", ", ".join(sorted(missing)))
        return 1
    with SessionLocal() as db:
        tenant_count = db.execute(text("SELECT COUNT(*) FROM tenants WHERE tenant_key LIKE 'R1_TENANT_%'")).scalar_one()
        user_count = db.execute(text("SELECT COUNT(*) FROM auth_users WHERE username LIKE 'r1-user-%@synthetic.invalid'")).scalar_one()
        duplicate_memberships = db.execute(text("SELECT COUNT(*) FROM (SELECT tenant_id, user_id FROM tenant_memberships GROUP BY tenant_id, user_id HAVING COUNT(*) > 1) x")).scalar_one()
        cross_tenant_users = db.execute(text("SELECT COUNT(*) FROM tenant_memberships m JOIN auth_users u ON u.id=m.user_id WHERE m.tenant_id<>u.tenant_id")).scalar_one()
    print(f"DAY35_SCHEMA = PASS ({len(REQUIRED_TABLES)} required tables)")
    print(f"DAY35_FIXTURE_TENANTS = {tenant_count}")
    print(f"DAY35_FIXTURE_USERS = {user_count}")
    print(f"DAY35_DUPLICATE_MEMBERSHIPS = {duplicate_memberships}")
    print(f"DAY35_CROSS_TENANT_MEMBERSHIPS = {cross_tenant_users}")
    return 0 if duplicate_memberships == 0 and cross_tenant_users == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
