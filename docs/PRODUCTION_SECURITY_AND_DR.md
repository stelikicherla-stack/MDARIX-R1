# Production security, deployment, performance and DR checklist

## Security gate

- Store database, SMTP, provider, GenAI and connector secrets in an approved
  secret manager; never commit `.env` files or provider keys.
- Use the non-superuser runtime role and rotate credentials through the secret
  manager.
- Terminate HTTPS at the approved reverse proxy and set secure, HttpOnly,
  SameSite cookies. Keep `MDARIX_ENABLE_API_DOCS=false` in production.
- Keep the database private; permit only application/worker security groups.
- Apply WAF/DDoS controls and alert on authentication anomalies.
- Review access quarterly and remove shared accounts.

## Deployment gate

The repository provides Docker Compose, health checks, a dedicated outbox
worker, migrations, and GitHub Actions CI. A production deployment must add:

1. Image signing and registry promotion.
2. Environment-specific secret/config injection.
3. Readiness/liveness probes and worker heartbeat monitoring.
4. Blue/green or rolling deployment with a tested rollback revision.
5. Database migration backup and forward/rollback approval.

## Performance gate

Run `python scripts/benchmark_api.py --base-url http://127.0.0.1:8007` against
a representative seeded environment. Record p50, p95, p99, error rate,
concurrency, database timings, vector-search timings, and storage growth. Do
not claim the target `<500ms p99` until the result is captured with dataset and
hardware versions.

## Disaster recovery gate

Target design: RPO 1 hour and RTO 4 hours, subject to partner approval.

- Daily encrypted full backup and frequent encrypted WAL archive.
- Isolated restore environment with no customer network access.
- Restore rehearsal, checksum verification, migration forward/rollback test,
  and point-in-time recovery to a recorded timestamp.
- Document owner, incident communication list, failover decision, and rollback.

Until encrypted backup storage, WAL archiving, restore infrastructure, TLS
certificates, and monitoring targets are supplied, these remain **PENDING —
production infrastructure required**.
