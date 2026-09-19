# MDARIX R1 — Day 32 Final Validation Report

DAY32 FINAL STATUS: COMPLETE

## Day 32 objective

Provide controlled scenario/counterfactual analysis and a structured Decision
Brief foundation. Scenario results are derived comparisons only; they do not
alter observed records or make regulated decisions.

## Day 31 entry gate

PASS. Day 31 is formally complete, its closure commit is pushed, and
`HEAD == origin/main` was verified before Day 32 work began.

## Implementation summary

- Reused the canonical `Scenario`, `AIExecution`, and `InvestigationBrief` models.
- Added controlled Day 32 scenario types and temporal validation.
- Added tenant-derived scenario execution at
  `/api/v1/investigations/{investigation_id}/scenarios`.
- Added explicit baseline, scenario, comparison, evidence, contradictions,
  unknowns, missing evidence, limitations, provenance, and human-review fields.
- Added scenario findings and scenario provenance to generated Decision Briefs.
- Read-only preview uses `persist=false`; source/business records are not changed.
- No frontend redesign, migration, or competing audit framework was introduced.

## Validation status

Focused validation was executed after rebuilding the project `.venv` with
Python 3.13: Day 32 scenario tests plus Day 16 counterfactual and Day 17 brief
regressions passed **14 passed, 0 failed** with two dependency deprecation
warnings. The fresh full backend regression then passed **297 passed, 0 failed,
0 errors** with two dependency deprecation warnings. The frontend production
build and Python compilation passed. `git diff --check` reported no whitespace
errors; only Windows line-ending warnings were emitted.

| Gate | Status |
|---|---|
| Scenario intelligence | PASS — authenticated live preview returned READY with persist=false |
| Counterfactual safety | PASS — derived scenario language; no causal/root-cause claim |
| Alternative hypotheses | PASS — uncertainty and limitations preserved |
| Decision Brief | PASS — authenticated Tenant A and Tenant B briefs generated |
| Tenant isolation | PASS — foreign brief access returned 404 |
| Temporal modes | PASS — CURRENT, EVENT, and KNOWN live checks returned requested modes |
| Dependency failure/recovery | PASS — 503 controlled failure and subsequent 200 recovery audited |
| Protected-domain nonmutation | PASS — protected-domain counts unchanged before/after |
| Backend regression | PASS — 297 passed, 0 failed, 0 errors |
| Frontend build | PASS |
| Python compilation | PASS |
| Diff check | PASS — no whitespace errors observed |

## Safety boundary

The result language explicitly preserves that scenarios are not observed
evidence, predictions, proof, or root-cause conclusions. Unknowns, missing
evidence, contradictions, and limitations remain separate fields. The broader
object audit framework remains an R1 cross-cutting backlog item.

## Live evidence

- Tenant A and Tenant B own-tenant scenario/brief execution succeeded.
- Tenant A access to the Tenant B investigation returned `404 INVESTIGATION_NOT_FOUND`.
- `DAY32_DEPENDENCY_FAILED` and `DAY32_SCENARIO_EXECUTED` were persisted with
  authenticated actor, server-derived tenant, correlation ID, operation details,
  and server timestamps.
- Audit secret scan returned `0` prohibited rows.
- Read-only scenario preview returned `id = null`; protected-domain counts did
  not change.

## GO / NO-GO

GO. Day 32 scenario/Decision Brief foundation and live validation gates are
complete. The broader platform-wide object audit framework remains an R1
cross-cutting backlog item and is outside Day 32 scope.
