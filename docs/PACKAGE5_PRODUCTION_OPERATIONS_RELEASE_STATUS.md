# Package 5 — Production operations and release readiness

## Verified locally

- Docker Compose configuration validates successfully.
- PostgreSQL 16/pgvector container is running and healthy.
- Database connectivity is confirmed for `mdarix_r1` using the configured local application role.
- GitHub Actions workflow is defined for backend migrations/tests/audit, frontend build/tests, dependency checks, and container validation.
- Two-instance verification tooling exists; production-like execution requires two running app processes against the same database.
- Health endpoints, outbox worker configuration, report/storage audit events, and rollback/release assurance documentation are present.

## Manual release gates

- Hosted GitHub Actions run and retained artifacts.
- Build and publish signed production images to the approved registry.
- Run two production-like application instances behind the approved reverse proxy/load balancer.
- Validate SMTP/Resend delivery, bounce handling, and inbound webhook signatures.
- Validate real external connector health/schema/pagination/cursor/retry/idempotency behavior.
- Use the approved non-superuser runtime database role and production secret manager.
- Validate PostgreSQL TLS, encrypted backups, restore, WAL/PITR, pooling, and monitoring.
- Configure production alert destinations and verify alert delivery.

## Rollback procedure

1. Stop promotion and record the release, migration, and incident identifiers.
2. Route traffic to the last known-good application image.
3. Do not roll back migrations destructively; use the reviewed forward-compatible migration or the approved Alembic downgrade procedure in an isolated rehearsal first.
4. Pause outbox delivery if the release can duplicate or misroute external messages.
5. Verify `/health/live`, `/health/ready`, database connectivity, session revocation, tenant isolation, and queue depth.
6. Reconcile failed/dead-lettered jobs and record the final audit evidence.

## Decision

Local readiness checks pass. Final production GO/NO-GO remains **PENDING** until the manual infrastructure and external-provider gates above have retained evidence.
