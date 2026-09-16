# MDARIX R1 Week 1 Requirement Inventory

Review scope: Day 0 through Day 7 only.

| ID | Source | Requirement | Category | Implementation | Test / Validation | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| W1-D0-001 | Day 0 | Windows local workspace at `C:\Users\user\Srinivas\MDARIX-R1` | Environment | Repository root | Git status, reports | PASS | Clean `main` review entry. |
| W1-D0-002 | Day 0 | Docker, Compose, Engine, PostgreSQL 16.15, pgvector 0.8.6 | Environment | `docker-compose.yml`, database | Day 0/2 validators | PASS | PostgreSQL container healthy; Day 2 validator PASS. |
| W1-D0-003 | Day 0 | Canonical R1 names: `mdarix-r1-postgres`, `mdarix-r1_default`, `mdarix-r1-postgres-data`, `localhost:5433` | Environment | `docker-compose.yml`, Day 0 report | Docker ps | PASS | Container healthy on `5433`. |
| W1-D0-004 | Day 0 | Python 3.13 venv with pg8000, SQLAlchemy, Alembic, Pydantic, pytest | Environment | `.venv`, `requirements.txt` | pytest, Alembic check | PASS | Full regression and Alembic check passed. |
| W1-D0-005 | Day 0 | GitHub private repo, `main`, secret exclusions | Source Control | `.gitignore`, origin | GitHub CLI, remote tree scan | PASS | Repo private; ignored artifacts not pushed. |
| W1-D1-001 | Day 1 | Product is core object; complaint must not become root object | Architecture | Backend APIs, Product 360 | Day 6/7 tests | PASS | Product list and Product 360 are product-centered. |
| W1-D1-002 | Day 1 | PostgreSQL-first Reality Graph; no Neo4j | Architecture | `graph/service.py`, migrations | Code scan | PASS | No Neo4j dependency. |
| W1-D1-003 | Day 1 | Evidence/provenance first; source truth preserved | Architecture | ingestion, normalization, provenance links | Day 4/5 tests, provenance review | PASS | Source records and source-canonical links preserved. |
| W1-D1-004 | Day 1 | Human authority and no Week 1 AI inference | Architecture | schema, no AI runtime | Code scan, tests | PASS | AI execution tables exist; deterministic flow uses no AI. |
| W1-D1-005 | Day 1 | Temporal-first architecture | Architecture | timestamps, Product 360 timeline | Day 7 tests | PASS | Event/effective/recorded/knowledge times exposed. |
| W1-D2-001 | Day 2 | Canonical tables and approved relationship entities exist | Database | Alembic migrations, SQLAlchemy models | Day 2 tests/validator | PASS | Required tables present. |
| W1-D2-002 | Day 2 | Tenant-scoped PK/FK/unique constraints | Database | migrations/models | Day 2 tests | PASS | Cross-tenant FK test passes. |
| W1-D2-003 | Day 2 | Source provenance, audit fields, JSONB/vector support | Database | schema/models | Day 2 validator | PASS | Source links, JSONB, vector present. |
| W1-D2-004 | Day 2 | AIExecution, HumanReview, Decision, Hypothesis remain distinct | Database | foundation models | Day 2 tests | PASS | Distinct entities tested. |
| W1-D3-001 | Day 3 | Controlled synthetic Golden Dataset with VS001-VS012 | Data | `data/golden`, `evaluation/ground_truth` | Day 3 tests | PASS | 12 scenarios verified. |
| W1-D3-002 | Day 3 | Application data excludes Ground Truth answers | Data/Security | source/canonical data | Day 3-7 scans/tests | PASS | Ground Truth only in evaluation/tests/docs. |
| W1-D3-003 | Day 3 | Dataset includes missing, duplicate, ambiguous, conflicting, late information | Data Quality | golden source files | Day 3 tests | PASS | Scenario and anomaly tests pass. |
| W1-D4-001 | Day 4 | Multi-source ingestion with source preservation | Ingestion | `ingestion/services` | Day 4 tests/validator | PASS | 53 files discovered after review correction. |
| W1-D4-002 | Day 4 | Schema validation, quality issues, idempotency, Ground Truth rejection | Ingestion | adapters/service | Day 4 tests | PASS | Duplicate and invalid source tests pass. |
| W1-D5-001 | Day 5 | Canonical normalization and deterministic identity resolution | Normalization | `ingestion/normalization` | Day 5 tests/validator | PASS | Normalization links and relationships pass. |
| W1-D5-002 | Day 5 | No silent forced identity resolution | Identity | source-canonical links | Day 5 tests | PASS | Ambiguous/unresolved records preserved. |
| W1-D5-003 | Day 5 | Product-version component configuration materialized | Normalization | `product_components`, canonical relationships | Day 7 tests, review fix | PASS | Finding W1R-HIGH-001 fixed. |
| W1-D6-001 | Day 6 | Reality Graph API/service from canonical relationships | Graph | `graph/service.py`, backend routes | Day 6 tests/validator | PASS | Graph nodes/relationships tested. |
| W1-D6-002 | Day 6 | Graph connectivity is not causality | Graph/Safety | graph warnings/catalog | Day 6 tests/scans | PASS | No `CAUSE` relationship type. |
| W1-D7-001 | Day 7 | Product list and Product 360 backend/API/frontend | Product 360 | `backend/app/product360`, `frontend` | Day 7 tests, build, smoke | PASS | Day 7 tests pass. |
| W1-D7-002 | Day 7 | Lifecycle timeline and Temporal Reality | Temporal | Product360 service | Day 7 tests/validator | PASS | Known/event-as-of tests pass. |
| W1-D7-003 | Day 7 | No current-state/future leakage in as-of Product 360 sections | Temporal | Product360 filtering | Review tests | PASS | Added tests for section payload filtering. |
| W1-D7-004 | Day 7 | Data quality limitations and no causal conclusion visible | Safety | Product360 limitations | Day 7 tests | PASS | `NO_CAUSAL_CONCLUSION` present. |

Summary: 28 requirements reviewed; 28 PASS; 0 FAIL; 0 PARTIAL; 0 NOT VERIFIED.
