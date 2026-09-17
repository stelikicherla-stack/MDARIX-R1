# MDARIX R1 Day 15 Decision Center Validation Report

## Scope

Day 15 adds a controlled Decision Center on top of the persisted Day 8–14 investigation outputs. It does not make regulatory, CAPA, recall, reportability, release, or field-action decisions.

## Reused architecture

- `InvestigationWorkspaceService` supplies product, version, temporal, evidence, limitation, and provenance context.
- Existing `AIExecution` records supply the latest Investigator, Hypothesis, Challenger, Unknowns, and Failure Chain outputs.
- Existing `Decision`, `HumanReview`, and `AuditEvent` entities provide decision memory, mandatory human review, and audit records.
- A small additive migration adds Decision Center status, readiness, product/version, temporal, snapshot, and advisory references.

## Readiness

Readiness is deterministic and explainable. Material contradictions, unresolved material unknowns, incomplete failure chains, missing evidence, or missing persisted upstream outputs prevent a `SUFFICIENT_FOR_REVIEW` result. No numeric confidence or root-cause probability is generated.

## Human authority boundary

The advisory is persisted as an `AIExecution` and explicitly marked as advisory. Creating a decision requires an authorized identity, controlled option, rationale, and context snapshot. The decision remains `REQUIRES_REVIEW` until a separate HumanReview is recorded. Human disagreement is preserved through the review disposition and audit event.

## Safety and integrity

Every Decision Center service query is tenant scoped. Product and ProductVersion IDs are copied from the investigation workspace context. Temporal mode and as-of values are propagated into context, advisory, decision, and audit metadata. Ground Truth is not read by the Decision Center. Provenance references point to upstream AI executions and their evidence references; hidden chain-of-thought is not stored.

Day 14 temporal semantics remain intact: Product 360 may show zero investigations for a historical snapshot before the investigation opened, while live investigation access remains available through the tenant-scoped relationship route.

## Validation

- Migration: `alembic upgrade head` PASS.
- Frontend build: PASS.
- Day 15 targeted tests: 5 passed, 0 failed, 0 errors.
- Combined Day 7–14 target suite: 48 passed, 0 failed, 0 errors.
- Full regression: 188 collected, 188 passed, 0 failed, 0 errors, 0 skipped, 0 xfailed, 0 xpassed.
- OpenAPI/live PostgreSQL validation: Decision Context, AI Advisory, Decision capture, and Human Review returned successful responses for the current live `INV-001` UUID.
- Manual UI validation: pending human confirmation; checklist is in `docs/R1_DAY15_MANUAL_UI_VALIDATION_CHECKLIST.md`.

## Known limitations

The R1 development identity mechanism uses the submitted `authorized_by_ref` / `reviewer_ref` values because full authentication is not implemented. The Decision Center is advisory and review-governed; it does not execute downstream QMS, regulatory, supplier, CAPA, recall, or product-release actions.

## Manual UI action feedback remediation

The Investigation Workspace action handlers were present and the live APIs returned successful structured responses. The observed defect was a frontend feedback/state presentation gap: clicks did not expose loading, completion, empty/abstention, or backend-error state, and duplicate submissions were not disabled. The UI now preserves the selected investigation and temporal context, disables action buttons while running, ignores stale responses after context changes, and renders explicit status feedback. Empty hypotheses and unsupported failure chains are shown as controlled outcomes rather than blank sections.

Live INV-002 Event-as-of 2026-02-15 validation used the current UUID returned by PostgreSQL: `f94057fa-52aa-435d-8bb3-5299f2d27845`. Workspace, Analysis, Hypotheses, Unknowns, and Failure Chain returned HTTP 200. Analysis abstained for insufficient evidence; hypotheses returned three controlled competing hypotheses; Unknowns returned fifteen records; Failure Chain returned three records with preserved validation metadata and no future-information leakage.
