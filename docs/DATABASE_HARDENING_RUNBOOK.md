# MDARIX database hardening runbook

The hardening migration is opt-in because enabling RLS while the application
still connects as a superuser would create a false security result.

1. Create or obtain a dedicated non-superuser runtime role and a separate
   read-only role. Store credentials in the deployment secret manager.
2. Set `MDARIX_DB_HARDENING_APPLY=1` and run the migration with the current
   migration runner. Review the generated grants and RLS policy count.
3. Change `POSTGRES_USER` and `POSTGRES_PASSWORD` to the runtime credentials,
   restart one controlled application instance, and run the isolation suite.
4. Verify tenant context is set after authentication and that missing or
   foreign `app.tenant_id` returns no rows. Never accept a tenant ID from the
   client as authority.
5. Configure PostgreSQL TLS (`ssl=on`, trusted certificates, `sslmode=verify-full`)
   in the deployment, then validate it from the application host.
6. Configure connection-pool limits against the database connection budget.
7. Configure encrypted backups and WAL archiving, perform a restore rehearsal
   and PITR test in an isolated environment, and retain evidence.
8. Connect database, migration, pool, backup, and RLS alerts to the approved
   monitoring destination.

The local repository cannot truthfully mark TLS, backups, PITR, production
monitoring, or multi-instance behavior as passed without those external
targets and evidence.
