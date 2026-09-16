# MDARIX R1

MDARIX R1 development foundation for Commercial Release 1.

This repository currently contains Day 0 engineering foundation only. It does not contain product functionality, application tables, API endpoints, frontend pages, AI agents, investigation workflows, evidence engines, or decision engines.

## Local Development Prerequisites

- Windows 11
- Docker Desktop with Docker Compose
- Git
- GitHub CLI
- Node.js and npm
- Python 3.13 virtual environment at `.venv`

The project Python interpreter is:

```powershell
.\.venv\Scripts\python.exe
```

Global Python installations are not used by MDARIX R1.

## PostgreSQL Foundation

Day 0 uses PostgreSQL 16 with pgvector in Docker.

- Container: `mdarix-r1-postgres`
- Database: `mdarix_r1`
- Application role: `mdarix_app`
- Host port: `localhost:5433`
- Container port: `5432`
- Vector extension: `pgvector`

Start the database with Docker Compose from the repository root:

```powershell
docker compose up -d
```

If Docker is not available on the shell PATH, use the installed Docker CLI path or add it to the current session PATH.

## Environment Variables

Use `.env` locally and never commit it. `.env.example` contains placeholders only.

Required local variables:

```text
POSTGRES_DB=mdarix_r1
POSTGRES_USER=mdarix_app
POSTGRES_PASSWORD=CHANGE_ME
```

## Python Foundation

MDARIX R1 Windows development uses `pg8000` for PostgreSQL connectivity. `psycopg` is not required for this environment because Windows Application Control blocked its native DLL, and security controls must not be weakened.

Day 0 Python packages:

- pg8000
- python-dotenv
- SQLAlchemy
- Alembic
- Pydantic
- pytest

Verify Python imports:

```powershell
.\.venv\Scripts\python.exe -c "import pg8000, dotenv, sqlalchemy, alembic, pydantic, pytest; print('imports ok')"
```

Verify Python to PostgreSQL connectivity:

```powershell
.\.venv\Scripts\python.exe .\day0_db_test.py
```

Expected result includes:

- Database `mdarix_r1`
- User `mdarix_app`
- PostgreSQL 16
- pgvector enabled
- Vector SQL test passing

## Day 0 Scope

Day 0 is complete only when the reproducible engineering foundation passes validation. Product and business functionality begin after Day 0 and are not included in this foundation commit.
