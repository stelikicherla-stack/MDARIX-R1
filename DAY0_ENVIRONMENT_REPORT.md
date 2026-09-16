# MDARIX R1 Day 0 Environment Report

Generated for workspace:

```text
C:\Users\user\Srinivas\MDARIX-R1
```

## Machine Information

| Gate | Status | Evidence |
| --- | --- | --- |
| Windows environment | PASS | Microsoft Windows NT 10.0.26200.0 |
| PowerShell | PASS | 5.1.26100.9444 |
| Docker Desktop | PASS | Docker 29.8.0 |
| Docker Engine | PASS | Docker Desktop engine running |
| Docker Compose | PASS | Docker Compose v5.5.1 |

## Docker Information

| Gate | Status | Evidence |
| --- | --- | --- |
| Container exists | PASS | `mdarix-r1-postgres` |
| Container image | PASS | `pgvector/pgvector:pg16` |
| Container health | PASS | healthy |
| Restart policy | PASS | `unless-stopped` |
| Host mapping | PASS | `localhost:5433 -> container:5432` |
| Canonical network name | PASS | `mdarix-r1_default` |
| Canonical volume name | PASS | `mdarix-r1-postgres-data` |
| Data preservation | PASS | No volumes deleted; no `docker compose down -v` used |

The working Docker network and volume names are accepted as canonical for MDARIX R1 local development. The old targets `mdarix_default` and `mdarix_r1_postgres_data` are superseded and are not Day 0 blockers.

## PostgreSQL Information

| Gate | Status | Evidence |
| --- | --- | --- |
| Docker psql | PASS | Validated through `docker exec mdarix-r1-postgres psql ...` |
| Host Windows psql | NOT REQUIRED | Docker psql is the Day 0 administration path |
| PostgreSQL version | PASS | PostgreSQL 16.15 |
| Database | PASS | `mdarix_r1` |
| Application role | PASS | `mdarix_app` |
| pgvector | PASS | `vector 0.8.6` |
| Vector SQL operation | PASS | `SELECT '[1,2,3]'::vector` returns `[1,2,3]` |
| Application schema empty | PASS | Public schema table count is `0` |

## Python Information

| Gate | Status | Evidence |
| --- | --- | --- |
| Global Python 3.14 | NOT RELEVANT | MDARIX uses the project venv only |
| Project Python | PASS | Python 3.13.15 |
| Project interpreter | PASS | `.venv\Scripts\python.exe` |
| pip | PASS | pip 26.2.1 |
| pg8000 | PASS | 1.31.5 |
| python-dotenv | PASS | installed |
| SQLAlchemy | PASS | 2.0.54 |
| Alembic | PASS | 1.20.0 |
| Pydantic | PASS | 2.13.5 |
| pytest | PASS | 9.1.1 |
| psycopg | NOT REQUIRED | Blocked by Windows Application Control; security controls were not weakened |
| Python DB connectivity | PASS | Existing `day0_db_test.py` passes |

## Node Information

| Gate | Status | Evidence |
| --- | --- | --- |
| Node.js | PASS | v24.15.0 |
| npm | PASS | 11.12.1 via `cmd /c npm --version` |
| Frontend implementation | NOT REQUIRED | No React or frontend app created on Day 0 |

## Git Information

| Gate | Status | Evidence |
| --- | --- | --- |
| Git installed | PASS | git 2.54.0.windows.1 |
| Git identity | PASS | Global user.name and user.email configured |
| Repository initialized | PASS | Branch `main` |
| Safe directory | PASS | Validated using an exact workspace safe-directory override when needed |
| `.env` ignored | PASS | `.gitignore` includes `.env` |
| `.venv` ignored | PASS | `.gitignore` includes `.venv/` |
| Database backup ignored | PASS | `.gitignore` includes `mdarix-r1-day0-backup.sql` |

## GitHub Information

| Gate | Status | Evidence |
| --- | --- | --- |
| GitHub CLI installed | PASS | `gh` 2.101.0 at `C:\Program Files\GitHub CLI\gh.exe` |
| GitHub authentication | PASS | Authenticated as `stelikicherla-stack` |
| Repository visibility | PASS | `stelikicherla-stack/MDARIX-R1` is private |
| Origin | PASS | `https://github.com/stelikicherla-stack/MDARIX-R1.git` |
| Push | PASS | `main` pushed to GitHub |

## Validation Matrix

| Day 0 Gate | Status |
| --- | --- |
| Docker installed | PASS |
| Docker Engine running | PASS |
| Docker Compose working | PASS |
| PostgreSQL container healthy | PASS |
| Persistent volume present | PASS |
| Canonical volume name | PASS |
| Canonical network name | PASS |
| Port 5433 reachable | PASS |
| Database `mdarix_r1` exists | PASS |
| Role `mdarix_app` exists | PASS |
| pgvector installed | PASS |
| Vector SQL test works | PASS |
| Application schema empty | PASS |
| Project Python 3.13.15 | PASS |
| Required Python packages installed | PASS |
| psycopg | NOT REQUIRED |
| pg8000 | PASS |
| Python DB connectivity | PASS |
| Node verified | PASS |
| npm verified | PASS |
| Git initialized on `main` | PASS |
| Required folder tree present | PASS |
| README present | PASS |
| `.gitignore` present | PASS |
| `.env.example` present | PASS |
| Real `.env` ignored | PASS |
| GitHub CLI authenticated | PASS |
| Initial commit | PASS |
| Private GitHub repository | PASS |
| Push to GitHub | PASS |

## Folder Tree

```text
MDARIX-R1/
  .github/
    workflows/
  ai/
  backend/
  data/
  docs/
  evaluation/
  evidence/
  frontend/
  graph/
  ingestion/
  infrastructure/
    database/
      backups/
      migrations/
      scripts/
      seeds/
    docker/
  .env.example
  .gitignore
  DAY0_ENVIRONMENT_REPORT.md
  README.md
  day0_db_test.py
  docker-compose.yml
```

## Environment Variables

`.env.example` contains placeholders only:

```text
POSTGRES_DB=mdarix_r1
POSTGRES_USER=mdarix_app
POSTGRES_PASSWORD=CHANGE_ME
```

The real `.env` is ignored and must not be committed.

## Outstanding Issues

- None.

## Recommendations

- Keep the current working database intact.
- Do not rename, migrate, copy, recreate, or delete the working PostgreSQL volume merely to change its name.
- Do not begin product coding until all required gates, including GitHub repository push, pass.
