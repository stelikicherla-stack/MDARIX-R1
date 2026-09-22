# MDARIX R1 Future Architecture — Current State

Status: **Stage 1 audit baseline — implementation preserved; remediation deferred to Stage 2**

## Product and architecture

MDARIX is a modular-monolith FastAPI/SQLAlchemy/PostgreSQL application with a React/Vite frontend. The domain model already covers Product, ProductVersion, complaints, investigations, evidence, hypotheses, unknowns, failure chains, scenarios, decisions, assurance, governance, mappings, connectors, users, memberships, roles, permissions, plans, entitlements, approvals, and audit events.

The strongest existing product concept is the evidence-bounded investigation workflow: temporal context, provenance, contradiction, unknowns, human review, and causal restraint are represented in domain services and reports. The controlled Challenger, Unknowns, Failure Chain, Scenario, and embedding implementations are deterministic local engines for R1 validation; they are not yet production GenAI or commercial connector integrations.

## Component classification

| Component | Stage 1 classification | Finding |
|---|---|---|
| PostgreSQL/pgvector domain model | KEEP + HARDEN | Broad tenant-aware foundation; migration/runtime proof still required. |
| FastAPI application services | KEEP + HARDEN | Preserve domain services; consolidate request context and route protection. |
| Existing authenticated Ask, Challenger, Failure Chain, Scenario, and governance routes | KEEP + HARDEN | Good security direction; apply one shared context dependency. |
| Legacy Product360, graph, evidence, retrieval, investigation, decision, trust, evaluation, and counterfactual routes | REFACTOR | Several routes silently fall back to a synthetic tenant without authentication. |
| `auth.service.LocalAuthService` | REFACTOR | Sessions and tokens are process-memory state. |
| Admin/access router | REFACTOR | Functionally broad and currently a large god-router; dynamic update path needs typed commands and field-level audit. |
| `frontend/src/main.tsx` | REFACTOR | 976-line routing/application monolith; preserve behavior while extracting tested feature modules. |
| Deterministic AI/embedding engines | KEEP + HARDEN | Safe R1 baseline; position clearly as controlled intelligence, not production model capability. |
| File/REST/Database connector contracts | KEEP + HARDEN | Configuration-driven abstraction exists; live providers, secret manager, retries, and health operations remain. |
| Golden scenarios/evaluation artifacts | TEST/DEMO ONLY until final qualification | Current VS001–VS012 artifacts are explicitly deferred/review evidence. |
| Temporary pytest directories and ad-hoc artifacts | REMOVE AFTER REPLACEMENT | Repository hygiene is polluted; do not commit generated scratch output. |

## Current delivery state

- `main` is aligned with `origin/main` at the audit checkpoint.
- The worktree contains uncommitted authentication, email, access-control, and frontend changes. They are preserved and not modified by Stage 1.
- The README still describes a Day 0-only foundation and is materially stale.
- There are 49 Python test files and no frontend test files.
- Frontend dependencies use `latest`, creating uncontrolled reinstall drift.
- CI workflow files are placeholders only; no automated build/test/migration gate is active.
- Docker is unavailable in the current shell, the controlled `.venv` cannot execute, and the active global interpreter is Python 3.14.4 rather than the required Python 3.13.x.

## Target MVP interpretation

The MVP should be a design-partner-ready, read-only intelligence workflow for one regulated-product investigation: authenticated user → Product/ProductVersion → signal/complaint scope → investigation → evidence → Ask MDARIX → bounded analysis → human-reviewed Decision Brief → audit/provenance. External systems remain systems of record; no autonomous regulatory decision or external write-back is part of MVP.
