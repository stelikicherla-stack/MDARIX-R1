# MDARIX R1 Day 1 Architecture Freeze Report

## 1. Day 1 Status

PASS.

Day 1 completed Product + Architecture Freeze documentation only. No product code, database schema, API endpoints, UI screens, business workflows, AI agents, or seed data were implemented.

## 2. Product Scope Summary

R1 is the first three-week working vertical slice of MDARIX. The R1 capability is the MDARIX Reality Investigation Engine for Medical Device Lifecycle Investigation & Decision Intelligence.

Core R1 question: Can MDARIX correctly reconstruct a medical-device investigation and produce a trustworthy Reality Investigation Brief?

## 3. Architecture Summary

The baseline architecture is: user -> web application -> REST API -> application services -> controlled AI orchestrator -> Reality/Knowledge Services -> PostgreSQL 16 + pgvector + file storage abstraction.

MDARIX is a system of intelligence, not a system of record.

## 4. Domain Model Summary

Product is the core object. Canonical R1 entities include Tenant, Product, ProductVersion, Component, Supplier, ManufacturingSite, LotBatch, Requirement, Change, Complaint, Investigation, Risk, FailureMode, Control, Evidence, Hypothesis, Unknown, FailureChain, Scenario, Decision, AIExecution, and HumanReview.

## 5. Reality Graph Summary

The MDARIX Reality Graph represents objects, relationships, time, evidence, and contradictions. R1 uses PostgreSQL-first relationship abstractions, not Neo4j.

## 6. Temporal Model Summary

R1 distinguishes source, event, effective, recorded, ingestion, investigation, AI execution, and decision timestamps.

## 7. Evidence Model Summary

Evidence is first-class. The architecture distinguishes source fact, derived fact, AI inference, hypothesis, unknown, and human decision.

## 8. AI Architecture Summary

R1 uses one controlled AI orchestrator with logical specialists. AI outputs must be evidence grounded, attributable, versioned, auditable, reviewable, and reproducible where practical.

## 9. Human Governance Summary

AI recommends. Authorized humans decide. Material regulated decisions require human review.

## 10. UI Architecture Summary

The UI is investigation-centric and evidence-first. Primary screens include Decision Center, Investigation Workspace, Timeline, Reality Graph, Evidence Panel, Hypothesis Panel, AI Challenger, Unknowns Radar, Failure Chain, Counterfactual Analysis, and Investigation Brief.

## 11. API Summary

R1 API conventions use REST, JSON, `/api/v1/`, plural kebab-case resources, opaque IDs, ISO 8601 UTC timestamps, tenant context, audit context, pagination, filtering, sorting, and structured errors.

## 12. Security Summary

Security baseline covers tenant isolation, authentication, authorization, RBAC, least privilege, secrets, data protection, audit, AI provenance, input validation, file validation, prompt-injection defenses, leakage controls, and cross-tenant tests.

## 13. Evaluation Summary

Evaluation uses Golden Dataset, Ground Truth, Golden Scenarios, and controlled measurement. Primary KPI is time-to-decision.

## 14. Golden Scenarios Summary

Twelve scenario IDs are frozen: VS001 through VS012, covering supplier correlation, false correlation, missing evidence, conflicting evidence, incorrect timeline, shared components, premature closure, control failure, counterfactuals, AI model change, multiple causes, and correct abstention.

## 15. Architecture Decisions

Created ADR-001 through ADR-010 with status PROPOSED.

## 16. Open Decisions

No blocking open decisions.

Non-blocking future decisions:

- Whether a graph database is needed after R1 evidence proves PostgreSQL-first insufficient.
- Whether LangGraph adds concrete orchestration value after the controlled orchestrator contract is implemented.
- Which production object/file storage provider to use beyond the local abstraction.

## 17. Files Created/Modified

- `README.md`
- `docs/R1_PRODUCT_SCOPE.md`
- `docs/R1_ARCHITECTURE_SPEC.md`
- `docs/R1_DOMAIN_MODEL.md`
- `docs/R1_AI_ARCHITECTURE.md`
- `docs/R1_REALITY_GRAPH_SPEC.md`
- `docs/R1_TEMPORAL_MODEL.md`
- `docs/R1_EVIDENCE_MODEL.md`
- `docs/R1_API_CONVENTIONS.md`
- `docs/R1_UI_INFORMATION_ARCHITECTURE.md`
- `docs/R1_SECURITY_BASELINE.md`
- `docs/R1_EVALUATION_STRATEGY.md`
- `docs/R1_GOLDEN_SCENARIOS.md`
- `docs/R1_ACCEPTANCE_CRITERIA.md`
- `docs/R1_DAY2_IMPLEMENTATION_CONTRACT.md`
- `docs/adr/ADR-001-system-of-intelligence.md`
- `docs/adr/ADR-002-product-as-core-object.md`
- `docs/adr/ADR-003-postgresql-first-reality-graph.md`
- `docs/adr/ADR-004-pgvector-semantic-retrieval.md`
- `docs/adr/ADR-005-single-controlled-ai-orchestrator.md`
- `docs/adr/ADR-006-human-authority.md`
- `docs/adr/ADR-007-evidence-provenance-first-ai.md`
- `docs/adr/ADR-008-temporal-first-class.md`
- `docs/adr/ADR-009-pg8000-windows-local.md`
- `docs/adr/ADR-010-r1-scope-vs-later-release.md`
- `docs/diagrams/01-system-context.mmd`
- `docs/diagrams/02-logical-architecture.mmd`
- `docs/diagrams/03-reality-graph.mmd`
- `docs/diagrams/04-ai-orchestration.mmd`
- `docs/diagrams/05-investigation-workflow.mmd`
- `docs/diagrams/06-evidence-provenance-flow.mmd`
- `docs/diagrams/07-primary-user-journey.mmd`
- `docs/diagrams/08-local-development-deployment.mmd`

## 18. Validation Matrix

| Gate | Status | Evidence |
| --- | --- | --- |
| Day 0 prerequisite | PASS | Day 0 report and live checks passed |
| R1 product scope | PASS | `R1_PRODUCT_SCOPE.md` |
| R1 out-of-scope | PASS | `R1_PRODUCT_SCOPE.md` |
| Primary user | PASS | `R1_PRODUCT_SCOPE.md` |
| Primary journey | PASS | `R1_PRODUCT_SCOPE.md`, journey diagram |
| Core object = Product | PASS | `R1_PRODUCT_SCOPE.md`, ADR-002 |
| System of Intelligence principle | PASS | `R1_ARCHITECTURE_SPEC.md`, ADR-001 |
| Domain model | PASS | `R1_DOMAIN_MODEL.md` |
| Reality Graph architecture | PASS | `R1_REALITY_GRAPH_SPEC.md` |
| Temporal architecture | PASS | `R1_TEMPORAL_MODEL.md`, ADR-008 |
| Evidence architecture | PASS | `R1_EVIDENCE_MODEL.md` |
| Hypothesis architecture | PASS | `R1_EVIDENCE_MODEL.md` |
| Unknown model | PASS | `R1_EVIDENCE_MODEL.md` |
| Failure Chain architecture | PASS | `R1_EVIDENCE_MODEL.md` |
| Counterfactual boundary | PASS | `R1_EVIDENCE_MODEL.md` |
| AI orchestration | PASS | `R1_AI_ARCHITECTURE.md`, ADR-005 |
| Human authority | PASS | `R1_AI_ARCHITECTURE.md`, ADR-006 |
| AI provenance | PASS | `R1_AI_ARCHITECTURE.md`, ADR-007 |
| API conventions | PASS | `R1_API_CONVENTIONS.md` |
| UI architecture | PASS | `R1_UI_INFORMATION_ARCHITECTURE.md` |
| Security baseline | PASS | `R1_SECURITY_BASELINE.md` |
| Evaluation architecture | PASS | `R1_EVALUATION_STRATEGY.md` |
| Golden Scenarios | PASS | `R1_GOLDEN_SCENARIOS.md` |
| Acceptance criteria | PASS | `R1_ACCEPTANCE_CRITERIA.md` |
| Repository ownership | PASS | `R1_ARCHITECTURE_SPEC.md` |
| Architecture diagrams | PASS | 8 Mermaid source diagrams |
| ADRs | PASS | ADR-001 through ADR-010 |
| Day 2 contract | PASS | `R1_DAY2_IMPLEMENTATION_CONTRACT.md` |
| Cross-document consistency | PASS | Terminology and scope scan completed |
| Git status | PASS | To be clean after Day 1 commit/push |
| Secret scan | PASS | `.env`, `.venv`, and Day 0 backup remain ignored |

## 19. Git Commit/Push Status

Pending at report creation. Final status will be verified after commit and push.

## 20. Day 2 Readiness

Ready for Day 2 after Day 1 artifacts are committed and pushed. Day 2 scope is PostgreSQL foundation plus initial canonical schema.
