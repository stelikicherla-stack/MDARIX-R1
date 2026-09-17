# MDARIX R1 — Day 25 Final Validation Report

## Scope

This report records the Day 25 final-validation attempt from checkpoint `76139d2`.
Day 23 remains explicitly excluded. No Day 26 work was started.

## Preflight

| Check | Result | Evidence |
|---|---|---|
| Branch | PASS | `main` |
| Checkpoint | PASS | `76139d2` is present at `HEAD` |
| Migration graph | PASS (static) | `i25enterprise` is the single Alembic head |
| Working tree | PASS | Only pre-existing pytest/artifact directories are untracked |
| Docker/PostgreSQL availability | BLOCKED | Docker CLI is unavailable in the execution environment |

## Application-level validation

| Gate | Result | Evidence |
|---|---|---|
| Day 25 targeted security/foundation tests | PASS | `17 passed` |
| Frontend production build | PASS | `npm.cmd --prefix frontend run build` |
| Diff whitespace check | PASS | `git diff --check` |
| Full backend regression | BLOCKED | Test run waits on the unavailable PostgreSQL dependency |

The targeted tests cover the AI data boundary, retention/disposition, controlled
export, connector reliability, connector isolation behavior, operations health,
and configuration lifecycle fail-closed behavior.

## Infrastructure gates

The following required gates could not be executed because Docker is not installed
or available on this host:

- Execute Alembic migration `i25enterprise` against the real MDARIX PostgreSQL database.
- Validate migrated tables, foreign keys, tenant constraints, indexes, and representative data.
- Create a post-migration PostgreSQL backup and record its checksum.
- Restore that backup into an isolated temporary target.
- Verify restored data, extensions, relationships, and audit records.
- Confirm active database and volume isolation during restore.
- Run the full backend regression against the migrated database.

These gates remain **BLOCKED**, not passed. No database, Docker container, volume,
or backup artifact was modified by this validation attempt.

## Day 25 status

Day 25 is **NOT COMPLETE / BLOCKED ON HOST INFRASTRUCTURE VALIDATION**.
The implementation checkpoint is stable at `76139d2`, and the application-level
Day 25 checks are green. Completion requires a host with Docker and the configured
PostgreSQL service, followed by migration, backup, isolated restore, restore
verification, full regression, and final Git review.

## Blocker recovery attempt

The prescribed recovery preflight was rerun on 2026-09-18:

```text
docker version
docker context show
docker ps
docker ps -a
```

All commands failed because `docker` is not installed or available on this host.
Per the recovery procedure, no Docker installation, reset, container start,
volume operation, database recreation, migration execution, backup, or restore
was attempted.

Therefore the recovery result remains:

**DAY 25 BLOCKED — Docker/PostgreSQL host infrastructure unavailable.**

## Recovery evidence supplied from the verified host

The subsequent host validation confirmed that the R1 PostgreSQL container was
healthy and that migration `i25enterprise` executed successfully from
`h23d4e5f6a01`. The full backend regression subsequently completed with
`252 passed, 0 failed, 0 errors`.

The isolated restore target
`mdarix_day25_restore_20260918_013318` was independently queried and verified:

- representative row counts matched the active database;
- 66 public tables were present;
- connector run, source-record, and reconciliation tables were present;
- representative product, investigation, complaint, and evidence relationships
  had zero orphaned rows;
- Alembic revision was `i25enterprise`;
- pgvector extension was present at version `0.8.6`.

This establishes **isolated restore and restored-schema verification as PASS**.
Backup artifact metadata/checksum, final security zero-gate evidence, and Day 26
readiness evidence remain required before the completion decision.

## Superseding host verification

The user subsequently verified Docker manually from Windows PowerShell:

- Docker Client `29.8.0`
- Docker Desktop Server `4.91.0`
- Context `desktop-linux`
- `mdarix-r1-postgres` healthy, `pgvector/pgvector:pg16`, host port `5433`
- `mdarix-postgres` is a separate container and is explicitly out of scope

This supersedes the earlier host-level conclusion. Docker is available on the
host but is not accessible from the Codex execution environment. The remaining
database, backup, isolated-restore, and full-regression gates must therefore be
run from the user's Windows PowerShell using only `mdarix-r1-postgres` and
database `mdarix_r1`.
