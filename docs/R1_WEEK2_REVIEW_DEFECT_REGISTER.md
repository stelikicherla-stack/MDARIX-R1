# R1 Week 2 Review Defect Register

## Day 14 Round 3 live investigation relationship remediation

The live PostgreSQL records are correctly linked: `INV-001` through `INV-007` belong to AsterFlow product `PRD-ASTER-100` under the ACME synthetic tenant. The browser's Event-as-of date was `2026-02-15`, while these investigations open on or after `2026-02-23`; Product 360 therefore correctly returned an empty historical set.

The Investigation access view must not interpret that historical absence as an absent association. A new tenant-scoped product-investigations route returns the real associated records for workspace selection, while Product 360 retains its temporal filtering. Evidence remains separately tenant-scoped. Backend restart and manual browser validation remain pending.

| ID | Severity | Classification | Finding | Remediation | Status |
|---|---|---|---|---|---|
| W2-UI-001 | Medium | UI defect | Challenger output was not previously rendered in the existing investigation screen | Added Challenger API invocation and material challenge panel in `frontend/src/main.tsx`; frontend build rerun | REMEDIATED + VERIFIED |
| W2-HOST-001 | High | Host-required validation gap | Real PostgreSQL/API/HTTP pipeline unavailable in agent environment | Added safe Windows host validator and explicit checklist; requires host execution | OPEN / HOST_REQUIRED |
| W2-UI-002 | Medium | UI validation gap | Browser/manual state validation cannot run in agent environment | Host checklist provided; no result fabricated | OPEN / HOST_REQUIRED |
| W2-UI-003 | Medium | UI defect | Investigations and Evidence navigation entries were non-interactive spans, preventing access to the existing Day 8–14 workspace | Added scroll navigation to the existing workspace/evidence sections; marked Decision Center as Day 15 unavailable | REMEDIATED + VERIFIED |
