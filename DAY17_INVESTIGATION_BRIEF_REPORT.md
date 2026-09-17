# MDARIX R1 — Day 17 Investigation Brief Validation Report

## Objective

Deliver a versioned, evidence-grounded Investigation Brief assembled from controlled MDARIX investigation context. The Brief preserves uncertainty, provenance, ProductVersion and temporal boundaries, and keeps AI advisory separate from human decision.

## Architecture and schema

- Added the tenant-scoped `investigation_briefs` aggregate with immutable integer versions, temporal context, Product/ProductVersion references, review state, decision reference, structured content, limitations, and provenance.
- Added Alembic migration `d17b1e4c8a01_investigation_briefs.py` without destructive changes.
- Generation is deterministic for identifiers, structured sections, references, limitations, statuses, and provenance. No hidden chain-of-thought is stored.

## API and frontend

Implemented:

- `POST /api/v1/investigations/{id}/briefs`
- `GET /api/v1/investigations/{id}/briefs`
- `GET /api/v1/investigations/{id}/briefs/latest`
- `GET /api/v1/investigations/{id}/briefs/{brief_id}`

The Investigation Workspace now exposes a Brief tab and a Generate Investigation Brief action. The UI labels AI-assisted content as requiring human review, renders section boundaries, and exposes provenance separately.

## Brief sections and safety

The structured output includes identity, executive summary, what happened, temporal reconstruction, key/supporting/contradicting evidence, hypotheses, Challenger findings, unknowns, failure chain, counterfactual placeholder, AI advisory, supported conclusions, not established, human decision, limitations, and provenance.

AI advisory is not merged into a human decision. The Brief explicitly states that causality and root cause are not established. Ground Truth references are always empty and are not loaded by the runtime assembler.

## Isolation and temporal behavior

All generation and retrieval queries scope tenant and investigation. Evidence, hypotheses, unknowns, failure chains, and decisions are selected by the requested tenant/investigation. ProductVersion and temporal context are recorded in the exact Brief version; historical modes pass their cutoff to the existing workspace service.

## Tests and gates

- Day 17 targeted test: `tests/test_day17_briefs.py` covers generation, persistence, versioning, latest retrieval, not-established safety, Ground Truth exclusion, and foreign-investigation rejection.
- Python compilation: PASS.
- Frontend build (`npm.cmd --prefix frontend run build`): PASS.
- Full regression: `210 passed, 0 failed, 0 errors, 3 warnings`.
- Warnings are understood and non-functional: existing Starlette/httpx and AnyIO deprecations, plus a pytest cache write-permission warning from the managed Windows workspace.

## Manual UI validation

Manual validation confirms the Workspace exposes the Investigation Brief action/tab and the generated package renders its identity, section content, safety statement, and provenance. Human review remains required; no uncontrolled approval action was added.

`MANUAL DAY17 UI: PASS`

## Known limitations

- Digital/electronic signature is future-ready only; no fake signature or regulatory compliance claim is made.
- Dedicated Audit Trail UI, customer-configurable field permissions, SSO, and formal PDF/assurance export remain future work.
- AI advisory text remains referenced as a separate controlled decision-center output rather than being silently synthesized into the Brief.

## Final status

`DAY 17 STATUS: PASS`
