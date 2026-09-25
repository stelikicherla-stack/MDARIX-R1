# Production Database Readiness Gates

Status: **PENDING — production infrastructure required**

No production claim is made for the database controls below. The current local
environment does not provide a confirmed production-like PostgreSQL target,
backup target, TLS material, or monitoring destination.

## Required prerequisites

- Managed PostgreSQL or a running PostgreSQL 16 server
- Separate application, migration, read-only, backup, and administration roles
- Production connection details and approved credentials
- TLS certificate authority and server certificate validation settings
- Encrypted backup and WAL/archive storage
- An isolated restore target
- Approved monitoring and alerting destinations
- Migration runner access with an auditable execution identity

## Closure gates

| Gate | Status | Required evidence |
| --- | --- | --- |
| Backup policy | **PENDING** | Automated encrypted backup configuration, retention, owner, and latest successful run |
| Restore rehearsal | **PENDING** | Restore into an isolated target and application verification |
| Point-in-time recovery | **PENDING** | WAL archive recovery to a selected timestamp before a test change |
| Migration forward/rollback | **PENDING** | Version check, pre-migration backup, forward run, rollback or documented compensating procedure, and post-checks |
| Connection pooling limits | **PENDING** | Pool configuration and evidence that aggregate instance connections remain below database limits |
| TLS enforcement | **PENDING** | Encrypted connection with certificate verification and rejection of non-TLS access |
| Database role separation | **PENDING** | Runtime, migration, reporting, backup, and administrative roles demonstrated separately |
| Least-privilege grants | **PENDING** | Runtime role cannot alter schema, create roles, or drop objects; grant report retained |
| Row-level security review | **PENDING** | Cross-tenant read/write denial tests at database and API layers |
| Retention and deletion policy | **PENDING** | Approved retention schedule, deletion behavior, audit preservation, and execution evidence |
| Production monitoring | **PENDING** | Availability, connections, slow queries, deadlocks, storage, backups, WAL lag, and security alerts |

## Required execution order

1. Provision the production-like PostgreSQL target and separate roles.
2. Configure TLS and verify certificate validation.
3. Apply and verify migrations using the migration role.
4. Verify runtime grants, pooling limits, and tenant isolation/RLS.
5. Configure encrypted backups and WAL archiving.
6. Perform restore rehearsal and point-in-time recovery.
7. Test migration forward and rollback/compensating procedures.
8. Configure monitoring, alert routing, and retention/deletion controls.
9. Run the full application and tenant-isolation regression suite.
10. Attach redacted logs, timestamps, database version, migration revision, and backup identifiers to the release report.

Until all gates have evidence, the release decision must retain the database
status as **PENDING — production infrastructure required**.
