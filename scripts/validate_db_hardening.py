"""Read-only database hardening gate; reports local facts and external gates."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine, text

from backend.app.db.session import database_url


def main() -> int:
    engine = create_engine(database_url(), future=True)
    with engine.connect() as conn:
        ssl = conn.execute(text("show ssl")).scalar()
        role = conn.execute(text("select current_user")).scalar()
        role_flags = conn.execute(text("select rolsuper, rolcreaterole, rolcreatedb from pg_roles where rolname=current_user")).one()
        rls_count = conn.execute(text("select count(*) from pg_class where relrowsecurity")).scalar()
        tenant_tables = conn.execute(text("select count(distinct table_name) from information_schema.columns where table_schema='public' and column_name='tenant_id'")).scalar()
        policies = conn.execute(text("select count(*) from pg_policies where policyname='mdarix_tenant_isolation'")).scalar()
        max_conn = conn.execute(text("show max_connections")).scalar()

    print(f"DATABASE = PASS ({role})")
    print(f"TENANT_TABLES = {tenant_tables}")
    print(f"RLS_POLICIES = {policies}; RLS_ENABLED_TABLES = {rls_count}")
    print(f"SSL = {'PASS' if str(ssl).lower() == 'on' else 'PENDING (ssl is off)'}")
    print(f"RUNTIME_ROLE = {'PASS' if not any(role_flags) else 'PENDING (current role is privileged)'}")
    print(f"POOL_LIMIT_REFERENCE = {max_conn} max_connections (application pool must be validated separately)")
    print("BACKUP_RESTORE_PITR = PENDING (approved backup/WAL target required)")
    print("MONITORING = PENDING (approved monitoring/alert destination required)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
