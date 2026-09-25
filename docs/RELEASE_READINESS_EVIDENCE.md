# MDARIX R1 Release-Readiness Evidence

Date: 2026-09-26

## Decision

**NO-GO for production/design-partner release evidence.**

The local production-like checks below pass, but production claims are not made
for browser evidence, hosted CI, TLS, backups/PITR, monitoring, or external
provider delivery until those environments are exercised.

## Automated evidence

| Gate | Result | Evidence |
|---|---|---|
| Frontend unit/component checks | PASS | `npm.cmd --prefix frontend test -- --run`; 3 files, 13 tests |
| Frontend production build | PASS | `npm.cmd --prefix frontend run build` |
| Request-context/connector/audit security tests | PASS | 7 tests passed |
| Two application instances/shared PostgreSQL | PASS | `scripts/verify_stage2_multi_instance.py` |
| Durable session reuse across instances | PASS | Same cookie accepted by instance 2 |
| Cross-instance revocation | PASS | Sign-out on instance 2 rejected the session on instance 1 |
| Local tenant-prefixed object storage | PASS | Write, signed URL, verification and tenant prefix |
| SMTP/provider configuration visibility | PASS | Local endpoint reported configured status |
| GenAI configuration visibility | PASS | Local endpoint reported configured status |
| REST connector | NOT CONFIGURED | No external REST endpoint/credential was supplied |

## Two-instance run

Command:

```powershell
.\.venv\Scripts\python.exe .\scripts\verify_stage2_multi_instance.py
```

Observed results:

```text
PASS | instance health | shared database reachable
PASS | session reuse
PASS | session revocation
PASS | object storage | tenant prefix, write, signed URL and verification
```

Session expiry was not exercised because it requires a controlled short-TTL
deployment or an isolated expiry fixture. Outbox retry/dead-letter execution
was not forced by this run.

## Evidence still required

### Browser and accessibility

Capture authenticated desktop and mobile screenshots for Platform Admin,
Customer Admin, Mapping Studio, and Decision approval. Record keyboard-only
focus order, visible focus, error states, and an NVDA/axe review. These require
a running browser session and cannot be honestly generated from backend tests.

### API traces and audit IDs

Run the authenticated workflows with correlation IDs and save redacted HTTP
requests/responses plus the corresponding audit-event IDs. Do not include
passwords, cookies, provider keys, or signed URLs in the evidence bundle.

### Migration and rollback

Record `alembic upgrade head`, schema verification, backup-before-migration,
forward migration, rollback/recovery procedure, and restore rehearsal against
the approved PostgreSQL environment.

### Security scans

Run and archive results for `pip-audit`, `npm audit`, Gitleaks, OWASP ZAP, and
the approved container scanner. A clean local test suite is not a substitute
for these scan artifacts.

### External and production operations

Still require approved targets and credentials for real SMTP/provider delivery,
customer connectors, object storage, TLS reverse proxy, hosted CI, monitoring,
multi-instance deployment, encrypted backups, restore/PITR, and connection
pooling validation.

## Rollback instructions

1. Stop the application and outbox worker deployment.
2. Preserve logs, correlation IDs, audit records, and migration output.
3. Restore the last approved application image/revision.
4. Restore the database only through the approved backup/PITR runbook when a
   schema rollback is required; do not edit production tables manually.
5. Re-run `/health/live`, `/health/ready`, migration consistency checks, tenant
   isolation checks, and smoke tests before reopening traffic.
6. Record the rollback owner, timestamp, reason, database recovery point, and
   verification results.

## Final status

Local automated release evidence is **partially complete**. The release is
**not GO** until the evidence gates above are executed and attached to the
versioned release report.
