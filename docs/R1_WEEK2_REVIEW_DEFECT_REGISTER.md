# R1 Week 2 Review Defect Register

| ID | Severity | Classification | Finding | Remediation | Status |
|---|---|---|---|---|---|
| W2-UI-001 | Medium | UI defect | Challenger output was not previously rendered in the existing investigation screen | Added Challenger API invocation and material challenge panel in `frontend/src/main.tsx`; frontend build rerun | REMEDIATED + VERIFIED |
| W2-HOST-001 | High | Host-required validation gap | Real PostgreSQL/API/HTTP pipeline unavailable in agent environment | Added safe Windows host validator and explicit checklist; requires host execution | OPEN / HOST_REQUIRED |
| W2-UI-002 | Medium | UI validation gap | Browser/manual state validation cannot run in agent environment | Host checklist provided; no result fabricated | OPEN / HOST_REQUIRED |
