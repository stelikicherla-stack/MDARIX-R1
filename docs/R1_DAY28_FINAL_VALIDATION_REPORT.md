# MDARIX R1 — Day 28 Final Validation Report

## Status

**CURRENT STATUS: DAY 28 COMPLETE / FROZEN — FINAL LIVE VALIDATION PASSED**

**DAY 28: IN PROGRESS — AUTHORIZED LIFECYCLE RETRIEVAL FOUNDATION**

Day 27 is formally complete and frozen at pushed HEAD `750e282`. Day 28 has
started; Day 29 has not started.

## Schema inventory

The existing PostgreSQL model already represents Product, ProductVersion,
Component, Supplier, ManufacturingSite, LotBatch, Requirement, Change,
Complaint, Investigation, Risk, FailureMode, Control, and Evidence. Existing
tenant-scoped relationship tables include ProductComponent, ComponentSupplier,
ProductSupplier, LotComponent, InvestigationComplaint, and
InvestigationEvidence. No migration or duplicate lifecycle model is required.

## Implementation

Added `LifecycleRetrievalService` with an authenticated tenant-scoped,
bounded retrieval contract. It preserves ProductVersion-to-Product ownership,
revalidates relationship tenant ownership, returns safe structured fields and
explicit relationship provenance, and labels relationships as non-causal.
The Day 27 Ask endpoint now accepts Complaint and Investigation scope IDs and
returns a bounded lifecycle neighborhood while preserving Day 27 retrieval
behavior and AI-safe controls.

Supported current relationships include ProductVersion → Component,
Component → Supplier, ProductVersion → Lot/Batch, ProductVersion → Requirement,
ProductVersion → Risk, Complaint → Investigation, and Investigation → Evidence
where represented by existing tables. Unsupported relationships are omitted;
no relationship is fabricated.

## Current validation

- Python compilation: PASS.
- Day 27 retrieval/API smoke subset: **9 passed, 0 failed, 0 errors**.
- Full Day 28 focused lifecycle matrix: **3 passed, 0 failed, 0 errors**.
- Lifecycle AI-safe context coverage: PASS; tenant identity is not exposed in
  model context and relationships remain explicitly non-causal.
- Live Tenant A/B lifecycle matrix: pending.
- Full backend regression: pending after Day 28 focused coverage.
- Frontend build: pending.
- Migration: NONE.

## Known limitations

- Day 28 does not implement temporal reconstruction, causal inference,
  hypotheses, failure-chain inference, or autonomous decisions.
- Some model entities have no direct relationship table and are reported as
  unavailable rather than inferred.
- Day 28 live proof must use the established synthetic Tenant A/B fixture.
- Live runtime, persisted audit, dependency-failure/recovery, nonmutation,
  full regression, and frontend build gates remain pending and must be proven
  before the Day 28 completion commit.

## Day 29 handoff

Day 29 remains **NOT STARTED** and is reserved for investigation timeline and
temporal reconstruction.

## Final validation update

- Day 28 focused lifecycle tests: **3 passed, 0 failed, 0 errors**.
- Day 28 plus Day 27 compatibility tests: **12 passed, 0 failed, 0 errors**.
- Golden dataset validator: **11 passed, 0 failed, 0 errors**.
- Frontend production build: **PASS**; pre-existing frontend changes were preserved.
- Python compilation for application, tests, and scripts: **PASS**.
- `git diff --check`: **PASS**.
- Clean complete backend regression: **290 passed, 0 failed, 0 errors, 3 warnings**.
- The earlier golden-data failure was reproduced as a compilation-method issue:
  broad repository compilation writes `.pyc` files into `data/golden`.
  The validated compilation method is scoped to `ask_mdarix backend tests scripts`
  and leaves **0** unexpected golden-data `.pyc` files.
- Live validation tooling prepared: the established Day 27 fixture now
  idempotently provisions symmetric synthetic Complaint, Investigation,
  Component, Supplier, and relationship records for both tenants. The live
  matrix now supports positive lifecycle retrieval and foreign relationship
  attack checks with Day 28 correlations.

## Automated coverage matrix

| Capability | Status |
|---|---|
| Complaint, Investigation, Product, Evidence retrieval | TESTED |
| ProductVersion integrity and wrong Product/ProductVersion pairing | TESTED |
| ProductVersion → Component relationship | TESTED |
| Component → Supplier relationship | TESTED |
| Provenance, bounded retrieval, partial results | TESTED |
| Non-causal relationship labeling | TESTED |
| AI-safe/pre-model context | TESTED |
| Tenant isolation and cross-tenant relationship traversal | TESTED |
| Lot/Batch, Requirement, Risk | NOT REPRESENTED IN CURRENT TEST FIXTURE |
| Nonmutation | PENDING LIVE VALIDATION |

The graph path is not a causal chain: **GRAPH PATH != CAUSAL CHAIN**.

## Remaining closure gates

Live Tenant A/B lifecycle retrieval, live relationship attack, persisted audit,
dependency failure/recovery, live nonmutation, and complete backend regression
remain pending because the Docker/database runtime is not accessible from the
Codex execution environment. These gates must be run from the verified Windows
PowerShell environment before Day 28 can be marked COMPLETE or committed.

**Live validation tooling prepared; execution pending in the authorized
Windows/Docker runtime.**

## Live validation results

The authorized Windows/Docker execution subsequently completed the Day 28
live gates:

- Tenant A lifecycle retrieval: **PASS**.
- Tenant B lifecycle retrieval: **PASS**.
- Symmetric foreign lifecycle relationship attacks: **PASS**; canary leakage
  was **0**.
- Persisted audit proof: **PASS**; authenticated actors and server-derived
  tenant IDs were retained for Day 28 correlations.
- Controlled dependency failure: **PASS**; HTTP 503 with
  `RETRIEVAL_UNAVAILABLE` and persisted `ASK_RETRIEVAL_FAILED`.
- Recovery after disabling the fault: **PASS**.
- Live nonmutation: **PASS**; before/after protected-record snapshots were
  identical.
- Post-live focused and compatibility tests: **12 passed, 0 failed, 0 errors**.
- Post-live golden dataset validator: **11 passed, 0 failed, 0 errors**.
- Authoritative post-live full backend regression: **290 passed, 0 failed,
  0 errors, 2 warnings**.
- Frontend production build: **PASS**.
- Scoped Python compilation: **PASS**; unexpected golden-data `.pyc`: **0**.
- `git diff --check`: **PASS**.

The live evidence confirms read-only lifecycle retrieval. Fixture provisioning,
audit rows, and session operational updates are legitimate operational writes;
protected lifecycle records did not change. **GRAPH PATH != CAUSAL CHAIN** and
**CORRELATION != CAUSATION** remain explicit boundaries.
