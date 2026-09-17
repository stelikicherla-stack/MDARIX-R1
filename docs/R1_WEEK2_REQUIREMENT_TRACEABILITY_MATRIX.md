# R1 Week 2 Requirement Traceability Matrix

| Requirement | Day | Contract/implementation | Test/evidence | Status |
|---|---:|---|---|---|
| Evidence observations retain source anchors | 8 | `evidence/`, `docs/R1_EVIDENCE_CLAIM_SEMANTICS.md` | Day 8 tests | PASS |
| Retrieval is tenant/version/temporal bounded | 9 | `retrieval/`, retrieval router | Day 9 tests; live host validation required | PARTIAL |
| Deterministic investigation context | 10 | `investigation_workspace/` | Day 10 tests | PASS |
| Investigator separates interpretations from facts | 11 | `investigator/` | Day 11 tests | PASS |
| Competing hypotheses preserve support/contradiction/gaps | 12 | `hypothesis_engine/` | Day 12 tests | PASS |
| Challenger tests evidence strength and causal leaps | 13 | `challenger/` | Day 13 tests | PASS |
| Unknowns remain distinct from negative facts | 14 | `unknowns/` | Day 14 semantic tests | PASS |
| Failure-chain links carry epistemic status and gaps | 14 | `failure_chain/` | Day 14 semantic tests | PASS |
| Day 8–14 live HTTP/database pipeline | 8–14 | Host validator and API routes | Docker/PostgreSQL unavailable | PARTIAL |
| Day 8–14 UI displays approved intelligence layers | 8–14 | `frontend/src/main.tsx` | Frontend build; manual checklist | PARTIAL |
| Tenant/temporal/version isolation through real boundaries | 8–14 | tenant-scoped services | Host validation required | PARTIAL |
| Ground Truth excluded from runtime | 8–14 | runtime modules and guardrails | static review; host review required | PARTIAL |

Overall: implementation is locally traceable, but live host gates remain open.
