# R1 Week 2 Live Integration Validation Report

## Environment

Workspace: `C:\Users\user\Srinivas\MDARIX-R1`.

Agent capability classification: Python/pytest/Node are available; Docker CLI, live PostgreSQL, and browser automation are unavailable. These are `HOST_REQUIRED`, not product failures or passes. A safe host validator is provided at `scripts/validation/validate_day14_host.ps1`.

Backend import and route registration were inspected from `backend.app.main`. The frontend production build completed successfully with `npm.cmd --prefix frontend run build`.

## Database and backend state

The repository expects PostgreSQL/pgvector through Docker at `localhost:5433` using `pg8000`. Docker is not installed or available in the validation shell (`docker` command not found), so a live PostgreSQL connection, migrations, persisted Golden Dataset, and real database writes could not be established in this run.

## API and UI implementation evidence

Day 8–Day 13 routers exist and Day 14 routes are registered through `backend.app.main`; Day 14 endpoints are:

- `POST/GET /api/v1/investigations/{id}/unknowns`
- `POST/GET /api/v1/investigations/{id}/failure-chains`

The frontend now exposes a controlled `Run Unknowns & Chain` action and renders Unknowns Radar and Failure Chain panels. Frontend TypeScript/Vite build: **PASS**.

Manual host UI procedure: `docs/R1_DAY14_HOST_UI_VALIDATION_CHECKLIST.md`.

## Automated validation

- Focused Day 12–Day 14 semantic suite: **14 passed**
- Complete available Python regression: **182 passed, 0 failed, 0 errors**

These results validate contracts and available automated behavior, but are not a substitute for live database/API execution.

## Required live gate status

| Requirement | Status | Evidence/limitation |
|---|---|---|
| Live database integration | BLOCKED | Docker/PostgreSQL unavailable in environment |
| Live API integration | BLOCKED | Real persistence cannot be established without database |
| Day 8–14 end-to-end pipeline | BLOCKED | Same infrastructure limitation |
| UI build | PASS | Vite production build succeeds |
| Manual UI validation | BLOCKED | No browser/computer-use session was available |
| Full automated regression | PASS | 182 passed, 0 failed, 0 errors |

## Security and semantic checks

The code preserves tenant propagation through the existing default-tenant API path, source/provenance fields, temporal snapshot fields, `UNKNOWN_GAP` chain links, contradiction references, and non-causal guardrails. No Ground Truth runtime import or remote synchronization was used.

## Conclusion

DAY 14 INTEGRATION CLOSURE BLOCKED — live PostgreSQL/API integration and manual UI validation remain unverified because Docker and a browser validation session are unavailable. No Day 14 commit or push should be performed until those gates are executed successfully.
