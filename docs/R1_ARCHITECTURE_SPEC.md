# MDARIX R1 Architecture Specification

## Status

PROPOSED for Day 1 architecture freeze.

## Logical Architecture

USER -> MDARIX WEB APPLICATION -> REST API -> APPLICATION SERVICES -> MDARIX AI ORCHESTRATOR -> REALITY / KNOWLEDGE SERVICES -> DATA LAYER.

## Application Services

Application services own product, investigation, evidence, hypothesis, unknown, failure-chain, scenario, decision, audit, and provenance workflows. They call domain services and AI/tool boundaries but retain deterministic validation, permission checks, transaction control, and audit obligations.

## AI Orchestrator

R1 uses one primary controlled orchestrator. Logical specialists are invoked as services/tools:

- Retrieval Specialist
- Timeline Specialist
- Evidence Specialist
- Hypothesis Specialist
- Challenger Specialist
- Unknowns Specialist
- Failure Chain Specialist
- Brief Specialist

These are not eight independently autonomous agents.

## Reality / Knowledge Services

- Reality Graph abstraction
- Temporal Reality Engine
- Evidence Store
- Vector Retrieval

Business logic must not depend directly on a graph database implementation.

## Data Layer

- PostgreSQL 16
- pgvector
- Object/file storage abstraction

PostgreSQL-first is the R1 baseline. Neo4j is excluded unless later evidence proves it necessary.

## Cross-Cutting Requirements

- Authentication and authorization
- Tenant isolation
- RBAC
- Audit trail
- AI provenance
- Observability
- Configuration
- Evaluation hooks
- Correlation/request IDs

## Technology Baseline

Frontend candidate: React, TypeScript, Tailwind CSS, shadcn/ui.

Backend: Python 3.13, FastAPI, SQLAlchemy, Alembic, Pydantic.

Local Windows PostgreSQL driver: pg8000.

Database: PostgreSQL 16 and pgvector.

Testing: pytest, API tests, Playwright later for UI E2E.

## Repository Boundaries

- `frontend/`: UI application.
- `backend/`: FastAPI application, APIs, domain/application services.
- `ai/`: orchestration, prompts/templates, AI abstractions.
- `data/`: Golden Dataset specifications and controlled synthetic fixtures.
- `ingestion/`: ingestion and normalization components.
- `evidence/`: evidence extraction and indexing services.
- `graph/`: Reality Graph abstractions and relationship logic.
- `evaluation/`: Golden Scenarios, Ground Truth, evaluation harness.
- `docs/`: architecture, ADRs, specifications.
- `infrastructure/`: Docker, database, migrations, deployment/configuration.

Duplicate business logic across directories is prohibited.

## Day 1 Boundary

Day 1 documents the architecture. It does not implement product features, APIs, database tables, UI screens, AI agents, or business workflows.
