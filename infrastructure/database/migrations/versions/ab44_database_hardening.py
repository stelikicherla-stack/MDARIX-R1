"""Create least-privilege runtime roles and tenant RLS policies.

This migration is intentionally opt-in.  It must not be applied accidentally
to a developer database because the application credentials must be switched
to the generated runtime role before RLS can safely deny missing context.
"""
import os

from alembic import op

revision = "ab44dbhardening"
down_revision = "aa43loginthrottles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if os.getenv("MDARIX_DB_HARDENING_APPLY", "").lower() not in {"1", "true", "yes"}:
        raise RuntimeError("Set MDARIX_DB_HARDENING_APPLY=1 to apply database hardening")

    op.execute("""
    DO $$
    BEGIN
      IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'mdarix_runtime') THEN
        CREATE ROLE mdarix_runtime NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
      END IF;
      IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'mdarix_readonly') THEN
        CREATE ROLE mdarix_readonly NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;
      END IF;
    END $$;
    GRANT USAGE ON SCHEMA public TO mdarix_runtime, mdarix_readonly;
    GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO mdarix_runtime;
    GRANT SELECT ON ALL TABLES IN SCHEMA public TO mdarix_readonly;
    GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO mdarix_runtime;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO mdarix_runtime;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO mdarix_readonly;
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO mdarix_runtime;
    """)

    # Auth bootstrap tables are deliberately excluded: the session token is
    # what establishes the tenant context before tenant RLS can be applied.
    op.execute("""
    DO $$
    DECLARE r record;
    BEGIN
      FOR r IN
        SELECT DISTINCT table_name
        FROM information_schema.columns
        WHERE table_schema = 'public' AND column_name = 'tenant_id'
          AND table_name NOT IN ('auth_users', 'auth_sessions')
      LOOP
        EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', r.table_name);
        EXECUTE format('ALTER TABLE public.%I FORCE ROW LEVEL SECURITY', r.table_name);
        EXECUTE format('DROP POLICY IF EXISTS mdarix_tenant_isolation ON public.%I', r.table_name);
        EXECUTE format(
          'CREATE POLICY mdarix_tenant_isolation ON public.%I USING (tenant_id = NULLIF(current_setting(''app.tenant_id'', true), '''')::uuid) WITH CHECK (tenant_id = NULLIF(current_setting(''app.tenant_id'', true), '''')::uuid)',
          r.table_name
        );
      END LOOP;
    END $$;
    """)


def downgrade() -> None:
    # Policies are removed, but roles are retained so rollback never deletes
    # credentials or ownership objects unexpectedly.
    op.execute("""
    DO $$
    DECLARE r record;
    BEGIN
      FOR r IN
        SELECT DISTINCT table_name
        FROM information_schema.columns
        WHERE table_schema = 'public' AND column_name = 'tenant_id'
          AND table_name NOT IN ('auth_users', 'auth_sessions')
      LOOP
        EXECUTE format('DROP POLICY IF EXISTS mdarix_tenant_isolation ON public.%I', r.table_name);
        EXECUTE format('ALTER TABLE public.%I NO FORCE ROW LEVEL SECURITY', r.table_name);
        EXECUTE format('ALTER TABLE public.%I DISABLE ROW LEVEL SECURITY', r.table_name);
      END LOOP;
    END $$;
    """)
