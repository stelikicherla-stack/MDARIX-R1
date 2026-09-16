# ADR-009: pg8000 for Windows R1 Local Development

## Context
Windows Application Control blocked psycopg native DLL use in the local environment.
## Decision
Use pg8000 for R1 Windows local development.
## Rationale
pg8000 passes Python to PostgreSQL connectivity without weakening security controls.
## Consequences
Day 2 database code and tests should use SQLAlchemy with pg8000 locally.
## Alternatives Considered
Disabling security controls or requiring psycopg locally was rejected.
## Status
PROPOSED
